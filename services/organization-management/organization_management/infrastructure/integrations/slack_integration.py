"""
Slack Integration Service
Handles creation and management of Slack channels and communication
"""
import asyncio
import json
import aiohttp
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from organization_management.domain.entities.meeting_room import MeetingRoom, MeetingPlatform, RoomType


@dataclass
class SlackCredentials:
    """Slack API credentials"""
    bot_token: str  # OAuth Bot User Token (xoxb-...)
    app_token: Optional[str] = None  # For Socket Mode (xapp-...)
    workspace_id: Optional[str] = None
    access_token: Optional[str] = None  # User token if needed
    webhook_url: Optional[str] = None  # For simple notifications


class SlackIntegrationService:
    """Service for Slack integration"""

    def __init__(self, credentials: SlackCredentials):
        self.credentials = credentials
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://slack.com/api"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                          use_form_data: bool = False) -> Dict:
        """Make authenticated request to Slack API"""
        if not self.session:
            raise Exception("Session not initialized. Use async context manager.")

        headers = {
            'Authorization': f'Bearer {self.credentials.bot_token}'
        }

        url = f"{self.base_url}/{endpoint}"

        try:
            if method.upper() == 'GET':
                async with self.session.get(url, headers=headers, params=data) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'POST':
                if use_form_data:
                    # Some Slack APIs require form data
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    async with self.session.post(url, headers=headers, data=data) as response:
                        return await self._handle_response(response)
                else:
                    headers['Content-Type'] = 'application/json'
                    async with self.session.post(url, headers=headers, json=data) as response:
                        return await self._handle_response(response)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except aiohttp.ClientError as e:
            self.logger.error(f"Slack API request failed: {e}")
            raise Exception(f"Slack API request failed: {e}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """Handle API response"""
        try:
            result = await response.json()

            # Slack API returns ok=true/false in the JSON response
            if result.get('ok'):
                return result
            else:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error(f"Slack API error: {error_msg}")
                raise Exception(f"Slack API error: {error_msg}")

        except aiohttp.ContentTypeError:
            error_text = await response.text()
            self.logger.error(f"Slack API error: {response.status} - {error_text}")
            raise Exception(f"Slack API error: {response.status} - {error_text}")

    async def create_meeting_room(self, room: MeetingRoom) -> Dict:
        """
        Create a Slack channel for the meeting room
        For Slack, a 'meeting room' translates to a dedicated channel
        """
        try:
            # Generate channel name (must be lowercase, no spaces, max 80 chars)
            channel_name = self._generate_channel_name(room)

            # Determine if channel should be private
            is_private = room.settings.get("private_channel", False)

            # Create the channel
            channel_data = {
                "name": channel_name,
                "is_private": is_private
            }

            # Add channel topic and description
            if room.name:
                channel_data["topic"] = room.name
                channel_data["purpose"] = f"Channel for {room.get_display_name()}"

            # Create channel
            result = await self._make_request('POST', 'conversations.create', channel_data)

            if result and result.get('channel'):
                channel = result['channel']
                channel_id = channel['id']

                # Set channel topic if it wasn't set during creation
                if room.name and not is_private:
                    await self.set_channel_topic(channel_id, room.name)

                # Set channel purpose/description
                purpose = f"Meeting room for {room.get_display_name()}"
                await self.set_channel_purpose(channel_id, purpose)

                # Enable huddles if requested
                if room.settings.get("enable_huddles", True):
                    self.logger.info(f"Huddles are enabled by default for channel {channel_id}")

                return {
                    "external_room_id": channel_id,
                    "join_url": f"slack://channel?team={self.credentials.workspace_id}&id={channel_id}",
                    "web_url": f"https://app.slack.com/client/{self.credentials.workspace_id}/{channel_id}",
                    "channel_name": channel['name'],
                    "is_private": channel.get('is_private', False),
                    "slack_data": channel
                }

            return {}

        except Exception as e:
            self.logger.error(f"Failed to create Slack channel: {e}")
            raise Exception(f"Failed to create Slack channel: {e}")

    def _generate_channel_name(self, room: MeetingRoom) -> str:
        """Generate Slack-compliant channel name"""
        # Base name
        if room.name:
            base = room.name.lower()
        else:
            type_map = {
                RoomType.TRACK_ROOM: "track",
                RoomType.INSTRUCTOR_ROOM: "instructor",
                RoomType.PROJECT_ROOM: "project",
                RoomType.ORGANIZATION_ROOM: "org"
            }
            base = f"{type_map.get(room.room_type, 'room')}"

        # Clean up name: only lowercase letters, numbers, hyphens, underscores
        import re
        cleaned = re.sub(r'[^a-z0-9-_]', '-', base)
        cleaned = re.sub(r'-+', '-', cleaned)  # Remove consecutive hyphens
        cleaned = cleaned.strip('-')  # Remove leading/trailing hyphens

        # Add identifier suffix to ensure uniqueness
        if room.track_id:
            suffix = str(room.track_id)[:8]
            cleaned = f"{cleaned}-{suffix}"
        elif room.project_id:
            suffix = str(room.project_id)[:8]
            cleaned = f"{cleaned}-{suffix}"
        elif room.instructor_id:
            suffix = str(room.instructor_id)[:8]
            cleaned = f"{cleaned}-instr-{suffix}"

        # Ensure max length of 80 characters
        return cleaned[:80]

    async def set_channel_topic(self, channel_id: str, topic: str) -> bool:
        """Set channel topic"""
        try:
            await self._make_request('POST', 'conversations.setTopic', {
                "channel": channel_id,
                "topic": topic[:250]  # Slack limit
            })
            return True
        except Exception as e:
            self.logger.warning(f"Failed to set channel topic: {e}")
            return False

    async def set_channel_purpose(self, channel_id: str, purpose: str) -> bool:
        """Set channel purpose/description"""
        try:
            await self._make_request('POST', 'conversations.setPurpose', {
                "channel": channel_id,
                "purpose": purpose[:250]  # Slack limit
            })
            return True
        except Exception as e:
            self.logger.warning(f"Failed to set channel purpose: {e}")
            return False

    async def update_meeting_room(self, room: MeetingRoom, slack_data: Dict) -> Dict:
        """Update existing Slack channel"""
        try:
            if not room.external_room_id:
                raise ValueError("Room must have external_room_id to update")

            # Update channel name if changed
            if room.name:
                new_name = self._generate_channel_name(room)
                await self._make_request('POST', 'conversations.rename', {
                    "channel": room.external_room_id,
                    "name": new_name
                })

            # Update topic and purpose
            if room.name:
                await self.set_channel_topic(room.external_room_id, room.name)

            purpose = f"Meeting room for {room.get_display_name()}"
            await self.set_channel_purpose(room.external_room_id, purpose)

            # Archive/unarchive based on status
            if room.status == "inactive":
                await self.archive_channel(room.external_room_id)
            elif slack_data.get('is_archived', False) and room.status == "active":
                await self.unarchive_channel(room.external_room_id)

            return {"success": True}

        except Exception as e:
            self.logger.error(f"Failed to update Slack channel: {e}")
            raise Exception(f"Failed to update Slack channel: {e}")

    async def archive_channel(self, channel_id: str) -> bool:
        """Archive a channel (soft delete)"""
        try:
            await self._make_request('POST', 'conversations.archive', {
                "channel": channel_id
            })
            return True
        except Exception as e:
            self.logger.error(f"Failed to archive channel: {e}")
            return False

    async def unarchive_channel(self, channel_id: str) -> bool:
        """Unarchive a channel"""
        try:
            await self._make_request('POST', 'conversations.unarchive', {
                "channel": channel_id
            })
            return True
        except Exception as e:
            self.logger.error(f"Failed to unarchive channel: {e}")
            return False

    async def delete_meeting_room(self, external_room_id: str) -> bool:
        """
        Delete Slack channel (archives it, as Slack doesn't truly delete channels)
        """
        return await self.archive_channel(external_room_id)

    async def get_meeting_room_info(self, external_room_id: str) -> Dict:
        """Get Slack channel information"""
        try:
            result = await self._make_request('POST', 'conversations.info', {
                "channel": external_room_id
            })
            return result.get('channel', {})

        except Exception as e:
            self.logger.error(f"Failed to get Slack channel info: {e}")
            return {}

    async def list_meeting_rooms(self) -> List[Dict]:
        """List all Slack channels"""
        try:
            result = await self._make_request('GET', 'conversations.list', {
                "exclude_archived": True,
                "types": "public_channel,private_channel"
            })
            return result.get('channels', [])

        except Exception as e:
            self.logger.error(f"Failed to list Slack channels: {e}")
            return []

    async def send_meeting_invitation(self, external_room_id: str, invitee_emails: List[str]) -> bool:
        """
        Invite users to Slack channel
        Note: Requires users to already be in the Slack workspace
        """
        try:
            # Look up users by email
            user_ids = []
            for email in invitee_emails:
                user_info = await self.get_user_by_email(email)
                if user_info and user_info.get('id'):
                    user_ids.append(user_info['id'])

            # Invite users to channel
            if user_ids:
                await self._make_request('POST', 'conversations.invite', {
                    "channel": external_room_id,
                    "users": ','.join(user_ids)
                })
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to send Slack channel invitation: {e}")
            return False

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Look up Slack user by email"""
        try:
            result = await self._make_request('GET', 'users.lookupByEmail', {
                "email": email
            })
            return result.get('user')

        except Exception as e:
            self.logger.warning(f"Failed to lookup user by email {email}: {e}")
            return None

    async def send_message(self, channel_id: str, text: str, blocks: Optional[List[Dict]] = None) -> Dict:
        """Send a message to a channel"""
        try:
            message_data = {
                "channel": channel_id,
                "text": text
            }

            if blocks:
                message_data["blocks"] = blocks

            result = await self._make_request('POST', 'chat.postMessage', message_data)
            return result

        except Exception as e:
            self.logger.error(f"Failed to send Slack message: {e}")
            return {}

    async def send_notification(self, channel_id: str, title: str, message: str,
                               color: str = "good") -> bool:
        """Send a formatted notification with attachment"""
        try:
            await self._make_request('POST', 'chat.postMessage', {
                "channel": channel_id,
                "text": title,
                "attachments": [{
                    "color": color,  # good (green), warning (yellow), danger (red), or hex
                    "text": message,
                    "footer": "Course Creator Platform",
                    "ts": int(datetime.utcnow().timestamp())
                }]
            })
            return True

        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def get_channel_members(self, channel_id: str) -> List[str]:
        """Get list of user IDs in a channel"""
        try:
            result = await self._make_request('GET', 'conversations.members', {
                "channel": channel_id
            })
            return result.get('members', [])

        except Exception as e:
            self.logger.error(f"Failed to get channel members: {e}")
            return []

    async def get_channel_history(self, channel_id: str, limit: int = 100) -> List[Dict]:
        """Get channel message history"""
        try:
            result = await self._make_request('GET', 'conversations.history', {
                "channel": channel_id,
                "limit": limit
            })
            return result.get('messages', [])

        except Exception as e:
            self.logger.error(f"Failed to get channel history: {e}")
            return []

    async def pin_message(self, channel_id: str, message_ts: str) -> bool:
        """Pin a message in a channel"""
        try:
            await self._make_request('POST', 'pins.add', {
                "channel": channel_id,
                "timestamp": message_ts
            })
            return True

        except Exception as e:
            self.logger.error(f"Failed to pin message: {e}")
            return False

    async def create_channel_bookmark(self, channel_id: str, title: str,
                                     link: str, emoji: str = ":link:") -> bool:
        """Add a bookmark to a channel"""
        try:
            await self._make_request('POST', 'bookmarks.add', {
                "channel_id": channel_id,
                "title": title,
                "type": "link",
                "link": link,
                "emoji": emoji
            })
            return True

        except Exception as e:
            self.logger.error(f"Failed to create bookmark: {e}")
            return False

    async def schedule_message(self, channel_id: str, text: str,
                              post_at: datetime) -> Dict:
        """Schedule a message to be sent later"""
        try:
            result = await self._make_request('POST', 'chat.scheduleMessage', {
                "channel": channel_id,
                "text": text,
                "post_at": int(post_at.timestamp())
            })
            return result

        except Exception as e:
            self.logger.error(f"Failed to schedule message: {e}")
            return {}

    async def start_huddle(self, channel_id: str) -> Dict:
        """
        Start a Slack Huddle in the channel
        Note: This is a newer Slack feature and may require specific permissions
        """
        try:
            # Slack Huddles are started by users, not bots
            # We can send a message encouraging users to start a huddle
            message = "🎙️ *Huddle Time!* Click the headphones icon in the bottom-left to start or join the huddle."
            result = await self.send_message(channel_id, message)
            return result

        except Exception as e:
            self.logger.error(f"Failed to start huddle: {e}")
            return {}

    def validate_configuration(self) -> bool:
        """Validate Slack integration configuration"""
        return bool(self.credentials.bot_token and
                   self.credentials.bot_token.startswith('xoxb-'))

    async def test_connection(self) -> Dict:
        """Test Slack API connection"""
        try:
            result = await self._make_request('POST', 'auth.test')
            return {
                "connected": True,
                "team": result.get('team'),
                "team_id": result.get('team_id'),
                "user": result.get('user'),
                "user_id": result.get('user_id'),
                "bot_id": result.get('bot_id')
            }

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return {"connected": False, "error": str(e)}
