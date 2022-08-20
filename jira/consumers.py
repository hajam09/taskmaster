import json

from channels.consumer import AsyncConsumer


# from chat.models import Thread, ChatMessage


class ChatConsumer(AsyncConsumer):
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
        # await self.create_chat_message(thread_obj, sent_by_user, msg)

        thisUser = self.scope['user']
        response = {
            'message': msg,
            'sender': {
                'id': thisUser.id,
                'fullName': thisUser.get_full_name(),
            },
            'sentBy': thisUser.id,
        }

        await self.channel_layer.group_send(
            self.chatRoom,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )

    async def websocket_disconnect(self, event):
        print('disconnect', event)

    async def chat_message(self, event):
        print('chat_message', event)

        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

    # @database_sync_to_async
    # def get_user_object(self, user_id):
    #     qs = User.objects.filter(id=user_id)
    #     if qs.exists():
    #         obj = qs.first()
    #     else:
    #         obj = None
    #     return obj

    # @database_sync_to_async
    # def get_thread(self, thread_id):
    #     qs = Thread.objects.filter(id=thread_id)
    #     if qs.exists():
    #         obj = qs.first()
    #     else:
    #         obj = None
    #     return obj

    # @database_sync_to_async
    # def create_chat_message(self, thread, user, msg):
    #     ChatMessage.objects.create(thread=thread, user=user, message=msg)
