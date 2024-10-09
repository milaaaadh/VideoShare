import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Video
from asgiref.sync import sync_to_async

class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.video_id = self.scope['url_route']['kwargs']['video_id']
        self.video_group_name = f'video_{self.video_id}'

        await self.channel_layer.group_add(
            self.video_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.video_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'increment_view':
            video = await self.increment_view_count(self.video_id)
            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    'type': 'video_view_update',
                    'views': video.views,
                }
            )

    async def video_view_update(self, event):
        views = event['views']

        await self.send(text_data=json.dumps({
            'views': views
        }))

    async def video_like_update(self, event):
        likes = event['likes']

        await self.send(text_data=json.dumps({
            'likes': likes
        }))

    @sync_to_async
    def increment_view_count(self, video_id):
        video = Video.objects.get(id=video_id)
        video.views += 1
        video.save()
        return video