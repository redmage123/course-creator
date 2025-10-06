"""
Microsoft Teams Integration Service
Handles creation and management of Teams meeting rooms
"""
import asyncio
import json
import aiohttp
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from domain.entities.meeting_room import MeetingRoom, MeetingPlatform, RoomType

@dataclass

class TeamsCredentials:
    """Teams API credentials"""
    tenant_id: str
    client_id: str
    client_secret: str
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class TeamsIntegrationService:
    """Service for Microsoft Teams integration"""

    def __init__(self, credentials: TeamsCredentials):
        self.credentials = credentials
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _get_access_token(self) -> str:
        """Get or refresh access token"""
        if (self.credentials.access_token and
            self.credentials.token_expires_at and
            datetime.utcnow() < self.credentials.token_expires_at - timedelta(minutes=5)):
            return self.credentials.access_token

        # Request new token
        token_url = f"https://login.microsoftonline.com/{self.credentials.tenant_id}/oauth2/v2.0/token"

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }

        async with self.session.post(token_url, data=data) as response:
            if response.status == 200:
                token_data = await response.json()
                self.credentials.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.credentials.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                return self.credentials.access_token
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get Teams access token: {response.status} - {error_text}")

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Teams API"""
        if not self.session:
            raise Exception("Session not initialized. Use async context manager.")

        token = await self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                async with self.session.get(url, headers=headers) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'POST':
                async with self.session.post(url, headers=headers, json=data) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'PUT':
                async with self.session.put(url, headers=headers, json=data) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'DELETE':
                async with self.session.delete(url, headers=headers) as response:
                    return await self._handle_response(response)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except aiohttp.ClientError as e:
            self.logger.error(f"Teams API request failed: {e}")
            raise Exception(f"Teams API request failed: {e}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """Handle API response"""
        if response.status in [200, 201, 202]:
            return await response.json()
        elif response.status == 404:
            return {}
        else:
            error_text = await response.text()
            self.logger.error(f"Teams API error: {response.status} - {error_text}")
            raise Exception(f"Teams API error: {response.status} - {error_text}")

    async def create_meeting_room(self, room: MeetingRoom) -> Dict:
        """Create a new Teams meeting room"""
        try:
            # Create online meeting
            meeting_data = {
                "subject": room.get_display_name(),
                "startDateTime": datetime.utcnow().isoformat() + "Z",
                "endDateTime": (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z",
                "isOnlineMeeting": True,
                "onlineMeetingProvider": "teamsForBusiness",
                "allowedPresenters": "organization",
                "recordAutomatically": room.settings.get("auto_recording", False),
                "allowAttendeeToEnableCamera": True,
                "allowAttendeeToEnableMic": True,
                "allowMeetingChat": "enabled" if room.settings.get("chat_enabled", True) else "disabled",
                "allowTeamworkReactions": True,
                "lobbyBypassSettings": {
                    "scope": room.settings.get("lobby_bypass", "organization"),
                    "isDialInBypassEnabled": False
                }
            }

            # If recurring meeting
            if room.is_recurring:
                meeting_data.update({
                    "recurrence": {
                        "pattern": {
                            "type": "weekly",
                            "interval": 1,
                            "daysOfWeek": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                        },
                        "range": {
                            "type": "endDate",
                            "startDate": datetime.utcnow().date().isoformat(),
                            "endDate": (datetime.utcnow() + timedelta(days=365)).date().isoformat()
                        }
                    }
                })

            # Create the meeting
            result = await self._make_request('POST', '/me/onlineMeetings', meeting_data)

            if result:
                return {
                    "external_room_id": result.get('id'),
                    "join_url": result.get('joinWebUrl'),
                    "meeting_id": result.get('videoTeleconferenceId'),
                    "conference_id": result.get('audioConferencing', {}).get('conferenceId'),
                    "dial_in_url": result.get('audioConferencing', {}).get('dialinUrl'),
                    "organizer_id": result.get('organizer', {}).get('identity', {}).get('user', {}).get('id'),
                    "creation_time": result.get('creationDateTime'),
                    "teams_data": result
                }

            return {}

        except Exception as e:
            self.logger.error(f"Failed to create Teams meeting room: {e}")
            raise Exception(f"Failed to create Teams meeting room: {e}")

    async def update_meeting_room(self, room: MeetingRoom, teams_data: Dict) -> Dict:
        """Update existing Teams meeting room"""
        try:
            if not room.external_room_id:
                raise ValueError("Room must have external_room_id to update")

            update_data = {
                "subject": room.get_display_name(),
                "allowedPresenters": "organization",
                "recordAutomatically": room.settings.get("auto_recording", False),
                "allowMeetingChat": "enabled" if room.settings.get("chat_enabled", True) else "disabled",
                "lobbyBypassSettings": {
                    "scope": room.settings.get("lobby_bypass", "organization"),
                    "isDialInBypassEnabled": False
                }
            }

            result = await self._make_request(
                'PATCH',
                f'/me/onlineMeetings/{room.external_room_id}',
                update_data
            )

            return result or {}

        except Exception as e:
            self.logger.error(f"Failed to update Teams meeting room: {e}")
            raise Exception(f"Failed to update Teams meeting room: {e}")

    async def delete_meeting_room(self, external_room_id: str) -> bool:
        """Delete Teams meeting room"""
        try:
            await self._make_request('DELETE', f'/me/onlineMeetings/{external_room_id}')
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete Teams meeting room: {e}")
            return False

    async def get_meeting_room_info(self, external_room_id: str) -> Dict:
        """Get Teams meeting room information"""
        try:
            result = await self._make_request('GET', f'/me/onlineMeetings/{external_room_id}')
            return result or {}

        except Exception as e:
            self.logger.error(f"Failed to get Teams meeting room info: {e}")
            return {}

    async def list_meeting_rooms(self) -> List[Dict]:
        """List all Teams meeting rooms"""
        try:
            result = await self._make_request('GET', '/me/onlineMeetings')
            return result.get('value', [])

        except Exception as e:
            self.logger.error(f"Failed to list Teams meeting rooms: {e}")
            return []

    async def get_meeting_attendance_report(self, external_room_id: str) -> Dict:
        """Get meeting attendance report"""
        try:
            # Note: This requires additional permissions and may not be available
            # for all meeting types
            result = await self._make_request('GET', f'/me/onlineMeetings/{external_room_id}/attendanceReports')
            return result or {}

        except Exception as e:
            self.logger.error(f"Failed to get Teams attendance report: {e}")
            return {}

    async def send_meeting_invitation(self, external_room_id: str, invitee_emails: List[str]) -> bool:
        """Send meeting invitation to users"""
        try:
            # Get meeting info first
            meeting_info = await self.get_meeting_room_info(external_room_id)
            if not meeting_info:
                return False

            # Create calendar event with meeting details
            event_data = {
                "subject": meeting_info.get('subject', 'Meeting Invitation'),
                "body": {
                    "contentType": "HTML",
                    "content": f"""
                    <p>You have been invited to join a Microsoft Teams meeting.</p>
                    <p><a href="{meeting_info.get('joinWebUrl')}">Join Microsoft Teams Meeting</a></p>
                    <p>Meeting ID: {meeting_info.get('videoTeleconferenceId', 'N/A')}</p>
                    """
                },
                "start": {
                    "dateTime": meeting_info.get('startDateTime', datetime.utcnow().isoformat()),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": meeting_info.get('endDateTime', (datetime.utcnow() + timedelta(hours=1)).isoformat()),
                    "timeZone": "UTC"
                },
                "attendees": [
                    {
                        "emailAddress": {
                            "address": email
                        },
                        "type": "required"
                    } for email in invitee_emails
                ],
                "onlineMeeting": {
                    "joinUrl": meeting_info.get('joinWebUrl')
                }
            }

            # Send calendar invitation
            await self._make_request('POST', '/me/events', event_data)
            return True

        except Exception as e:
            self.logger.error(f"Failed to send Teams meeting invitation: {e}")
            return False

    def validate_configuration(self) -> bool:
        """Validate Teams integration configuration"""
        return all([
            self.credentials.tenant_id,
            self.credentials.client_id,
            self.credentials.client_secret
        ])