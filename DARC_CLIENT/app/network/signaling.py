import asyncio, json, websockets
from config import SERVER_URL

class SignalingClient:
    def __init__(self, client_id, on_message):
        self.client_id = client_id
        self.on_message = on_message

    async def connect(self):
        self.ws = await websockets.connect(SERVER_URL)
        await self.ws.send(json.dumps({
            "type": "register",
            "client_id": self.client_id
        }))
        asyncio.create_task(self.listen())

    async def listen(self):
        async for msg in self.ws:
            data = json.loads(msg)
            self.on_message(data)

    async def send(self, to, payload):
        await self.ws.send(json.dumps({
            "type": "relay",
            "to": to,
            "payload": payload
        }))
