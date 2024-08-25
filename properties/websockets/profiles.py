from django.db import models
from accounts.models.users import User
from accounts.models.profiles import UserProfile
from properties.models.profiles import Profiles
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class CreateProfile(AsyncWebsocketConsumer):

    @sync_to_async
    def get_user_instance(self, user_query_id) -> models.Model:
        try:
            user_instance = User.get_user(query_id=user_query_id)
        except User.DoesNotExist:
            return None
        return user_instance.pk
    
    @sync_to_async
    def get_user_profile_instance(self, user_query_id) -> models.Model:
        try:
            user_profile_instance = UserProfile.get_profile(query_id=user_query_id)
        except UserProfile.DoesNotExist:
            return None
        return user_profile_instance
    
    @sync_to_async
    def create_profile(self, user_query_id, profile_data):
        user_instance = User.objects.get(pk=user_query_id)
        profile = Profiles.objects.create(
            user=user_instance
        )
        return profile

    async def connect(self):
        user_query_id = self.scope['url_route']['kwargs']['user_query_id']
        user_id = await self.get_user_instance(user_query_id=user_query_id)

        if user_id:
            await self.accept()
            await self.channel_layer.group_add(
                f"user_{user_id}",
                self.channel_name
            )
        else:
            await self.close()

    async def disconnect(self, close_code):
        user_query_id = self.scope['url_route']['kwargs']['user_query_id']
        user_id = await self.get_user_instance(user_query_id=user_query_id)

        if user_id:
            await self.channel_layer.group_discard(
                f"user_{user_id}",
                self.channel_name
            )

    async def receive(self, profile_data):
        """
        Method to handle incoming data from the WebSocket client.
        """
        profile_data_json = json.loads(profile_data)
        user_query_id = self.scope['url_route']['kwargs']['user_query_id']

        user_profile = await self.get_user_profile_instance(user_query_id, profile_data_json)
        
        if user_profile:
            await self.create_profile(user_query_id)
            await self.send(text_data=json.dumps({
                'status': 'success',
                'message': 'Profile created successfully.'
            }))
        else:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'User profile not found.'
            }))

    async def send_device_data(self, event):
        device_data = event['device_data']
        await self.send(text_data=json.dumps({'device_data': device_data}))
