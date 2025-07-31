"""
Zoom Integration Service
Handles creation and management of Zoom meeting rooms
"""
import asyncio
import json
import aiohttp
import base64
import jwt
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from domain.entities.meeting_room import MeetingRoom, MeetingPlatform, RoomType

@dataclass

class ZoomCredentials:
    """Zoom API credentials"""
    api_key: str
    api_secret: str
    account_id: Optional[str] = None
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class ZoomIntegrationService:
    """Service for Zoom integration"""

    def __init__(self, credentials: ZoomCredentials):
        self.credentials = credentials
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.zoom.us/v2"
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
        """Get or refresh access token using Server-to-Server OAuth"""
        if (self.credentials.access_token and
            self.credentials.token_expires_at and
            datetime.utcnow() < self.credentials.token_expires_at - timedelta(minutes=5)):
            return self.credentials.access_token

        # Use Server-to-Server OAuth
        token_url = "https://zoom.us/oauth/token"

        # Create basic auth header
        auth_header = base64.b64encode(
            f"{self.credentials.api_key}:{self.credentials.api_secret}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'account_credentials',
            'account_id': self.credentials.account_id or 'me'
        }

        async with self.session.post(token_url, headers=headers, data=data) as response:
            if response.status == 200:
                token_data = await response.json()
                self.credentials.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.credentials.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                return self.credentials.access_token
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get Zoom access token: {response.status} - {error_text}")

    def _generate_jwt_token(self) -> str:
        """Generate JWT token for legacy Zoom JWT authentication (deprecated)"""
        # This is for legacy JWT apps - new apps should use Server-to-Server OAuth
        payload = {
            'iss': self.credentials.api_key,
            'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            'iat': int(datetime.utcnow().timestamp()),
            'aud': 'zoom',
            'appKey': self.credentials.api_key,
            'tokenExp': int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            'alg': 'HS256'
        }

        return jwt.encode(payload, self.credentials.api_secret, algorithm='HS256')

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Zoom API"""
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
            elif method.upper() == 'PATCH':
                async with self.session.patch(url, headers=headers, json=data) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'DELETE':
                async with self.session.delete(url, headers=headers) as response:
                    return await self._handle_response(response)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except aiohttp.ClientError as e:
            self.logger.error(f"Zoom API request failed: {e}")
            raise Exception(f"Zoom API request failed: {e}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """Handle API response"""
        if response.status in [200, 201, 202, 204]:
            try:
                return await response.json()
            except aiohttp.ContentTypeError:
                return {}
        elif response.status == 404:
            return {}
        else:
            error_text = await response.text()
            self.logger.error(f"Zoom API error: {response.status} - {error_text}")
            raise Exception(f"Zoom API error: {response.status} - {error_text}")

    async def create_meeting_room(self, room: MeetingRoom) -> Dict:
        """Create a new Zoom meeting room"""
        try:
            # Determine meeting type
            meeting_type = 2  # Scheduled meeting
            if room.is_recurring:
                meeting_type = 8  # Recurring meeting with fixed time

            meeting_data = {
                "topic": room.get_display_name(),
                "type": meeting_type,
                "start_time": datetime.utcnow().isoformat() + "Z",
                "duration": 60,  # Default 60 minutes
                "timezone": "UTC",
                "password": room.passcode if room.passcode else None,
                "agenda": f"Meeting room for {room.get_display_name()}",
                "settings": {
                    "host_video": True,
                    "participant_video": room.settings.get("video_on_entry", True),
                    "cn_meeting": False,
                    "in_meeting": False,
                    "join_before_host": room.settings.get("join_before_host", False),
                    "mute_upon_entry": room.settings.get("mute_on_entry", True),
                    "watermark": False,
                    "use_pmi": False,
                    "approval_type": 2,  # No registration required
                    "registration_type": 1,
                    "audio": "both",
                    "auto_recording": "cloud" if room.settings.get("auto_recording", False) else "none",
                    "enforce_login": False,
                    "enforce_login_domains": "",
                    "alternative_hosts": "",
                    "close_registration": False,
                    "show_share_button": room.settings.get("allow_screen_sharing", True),
                    "allow_multiple_devices": True,
                    "registrants_confirmation_email": True,
                    "waiting_room": room.settings.get("waiting_room", True),
                    "request_permission_to_unmute_participants": True,
                    "meeting_authentication": False,
                    "breakout_room": {
                        "enable": room.settings.get("breakout_rooms_enabled", False)
                    }
                }
            }

            # Add recurrence for recurring meetings
            if room.is_recurring:
                meeting_data["recurrence"] = {
                    "type": 2,  # Weekly
                    "repeat_interval": 1,
                    "weekly_days": "1,2,3,4,5",  # Monday to Friday
                    "end_times": 52  # 52 weeks
                }

            # Create the meeting
            result = await self._make_request('POST', '/users/me/meetings', meeting_data)

            if result:
                return {
                    "external_room_id": str(result.get('id')),
                    "join_url": result.get('join_url'),
                    "host_url": result.get('start_url'),
                    "meeting_id": result.get('id'),
                    "passcode": result.get('password'),
                    "dial_in_numbers": result.get('settings', {}).get('global_dial_in_numbers', []),
                    "zoom_data": result
                }

            return {}

        except Exception as e:
            self.logger.error(f"Failed to create Zoom meeting room: {e}")
            raise Exception(f"Failed to create Zoom meeting room: {e}")

    async def update_meeting_room(self, room: MeetingRoom, zoom_data: Dict) -> Dict:
        """Update existing Zoom meeting room"""
        try:
            if not room.external_room_id:
                raise ValueError("Room must have external_room_id to update")

            update_data = {
                "topic": room.get_display_name(),
                "password": room.passcode if room.passcode else None,
                "settings": {
                    "host_video": True,
                    "participant_video": room.settings.get("video_on_entry", True),
                    "join_before_host": room.settings.get("join_before_host", False),
                    "mute_upon_entry": room.settings.get("mute_on_entry", True),
                    "auto_recording": "cloud" if room.settings.get("auto_recording", False) else "none",
                    "show_share_button": room.settings.get("allow_screen_sharing", True),
                    "waiting_room": room.settings.get("waiting_room", True),
                    "breakout_room": {
                        "enable": room.settings.get("breakout_rooms_enabled", False)
                    }
                }
            }

            result = await self._make_request(
                'PATCH',
                f'/meetings/{room.external_room_id}',
                update_data
            )

            return result or {}

        except Exception as e:
            self.logger.error(f"Failed to update Zoom meeting room: {e}")
            raise Exception(f"Failed to update Zoom meeting room: {e}")

    async def delete_meeting_room(self, external_room_id: str) -> bool:
        """Delete Zoom meeting room"""
        try:
            await self._make_request('DELETE', f'/meetings/{external_room_id}')
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete Zoom meeting room: {e}")
            return False

    async def get_meeting_room_info(self, external_room_id: str) -> Dict:
        """Get Zoom meeting room information"""
        try:
            result = await self._make_request('GET', f'/meetings/{external_room_id}')
            return result or {}

        except Exception as e:
            self.logger.error(f"Failed to get Zoom meeting room info: {e}")
            return {}

    async def list_meeting_rooms(self, user_id: str = 'me') -> List[Dict]:
        """List all Zoom meeting rooms"""
        try:
            result = await self._make_request('GET', f'/users/{user_id}/meetings')
            return result.get('meetings', [])

        except Exception as e:
            self.logger.error(f"Failed to list Zoom meeting rooms: {e}")
            return []

    async def get_meeting_participants(self, external_room_id: str) -> List[Dict]:
        """Get meeting participants (past meeting)"""
        try:
            result = await self._make_request('GET', f'/past_meetings/{external_room_id}/participants')
            return result.get('participants', [])

        except Exception as e:
            self.logger.error(f"Failed to get Zoom meeting participants: {e}")
            return []

    async def get_meeting_poll_results(self, external_room_id: str) -> List[Dict]:
        """Get meeting poll results"""
        try:
            result = await self._make_request('GET', f'/past_meetings/{external_room_id}/polls')
            return result.get('questions', [])

        except Exception as e:
            self.logger.error(f"Failed to get Zoom meeting polls: {e}")
            return []

    async def create_meeting_registration(self, external_room_id: str, registrant_info: Dict) -> Dict:
        """Create meeting registration"""
        try:
            result = await self._make_request(
                'POST',
                f'/meetings/{external_room_id}/registrants',
                registrant_info
            )
            return result or {}

        except Exception as e:
            self.logger.error(f"Failed to create Zoom meeting registration: {e}")
            return {}

    async def send_meeting_invitation(self, external_room_id: str, invitee_emails: List[str]) -> bool:
        """Send meeting invitation to users"""
        try:
            # Get meeting info first
            meeting_info = await self.get_meeting_room_info(external_room_id)
            if not meeting_info:
                return False

            # For each email, create a registration if registration is enabled
            for email in invitee_emails:
                registrant_data = {
                    "email": email,
                    "first_name": email.split('@')[0].title(),
                    "last_name": "User"
                }

                await self.create_meeting_registration(external_room_id, registrant_data)

            return True

        except Exception as e:
            self.logger.error(f"Failed to send Zoom meeting invitation: {e}")
            return False

    async def get_user_info(self, user_id: str = 'me') -> Dict:
        """Get Zoom user information"""
        try:
            result = await self._make_request('GET', f'/users/{user_id}')
            return result or {}

        except Exception as e:
            self.logger.error(f"Failed to get Zoom user info: {e}")
            return {}

    def validate_configuration(self) -> bool:
        """Validate Zoom integration configuration"""
        return all([
            self.credentials.api_key,
            self.credentials.api_secret
        ])