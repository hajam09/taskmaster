import json

from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

# from chat.models import Thread, ChatMessage
from accounts.models import TeamChatMessage, Team


class TeamChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('connected', event)
        roomId = self.scope['path'].split('/')[3]
        chatRoom = f'teamChatRoom{roomId}'

        self.chatRoom = chatRoom
        await self.channel_layer.group_add(
            chatRoom,
            self.channel_name
        )
        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_receive(self, event):
        print('receive', event)
        receivedData = json.loads(event['text'])
        msg = receivedData.get('message')

        if not msg:
            print('Error:: empty message')
            return False

        thisUser = self.scope['user']
        teamUrl = self.scope['url_route']['kwargs']['url']
        team = await self.getTeamObject(teamUrl)
        lastTeamChatMessage = await self.getLastTeamChatMessage()
        await self.createTeamChatMessage(team, thisUser, msg)

        today = timezone.datetime.today()
        hour = today.hour
        minute = today.minute
        meridiem = "am" if hour < 12 else "pm"

        response = {
            'id': lastTeamChatMessage.id + 1,
            'message': msg,
            'sender': {
                'id': thisUser.id,
                'fullName': thisUser.get_full_name(),
            },
            'time': f'{hour}:{minute} {meridiem}',
        }

        await self.channel_layer.group_send(
            self.chatRoom,
            {
                'type': 'teamChatMessage',
                'text': json.dumps(response)
            }
        )

    async def websocket_disconnect(self, event):
        print('disconnect', event)

    async def teamChatMessage(self, event):
        print('teamChatMessage', event)

        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

    @database_sync_to_async
    def getTeamObject(self, url):
        return Team.objects.filter(url__exact=url).first()

    @database_sync_to_async
    def getLastTeamChatMessage(self):
        return TeamChatMessage.objects.last()

    @database_sync_to_async
    def createTeamChatMessage(self, team, user, message):
        TeamChatMessage.objects.create(team=team, user=user, message=message)
