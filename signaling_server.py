import asyncio
import json
import websockets

# Stores: client_id -> websocket
CLIENTS = {}

async def handler(websocket):
    """
    Expected first message from client:
    {
        "type": "register",
        "client_id": "alice"
    }
    """

    client_id = None
    try:
        # First message must be registration
        raw = await websocket.recv()
        msg = json.loads(raw)

        if msg.get("type") != "register":
            await websocket.close()
            return

        client_id = msg["client_id"]
        CLIENTS[client_id] = websocket
        print(f"[+] {client_id} connected")

        # Notify others
        await broadcast_user_list()

        # Handle messages
        async for raw_msg in websocket:
            data = json.loads(raw_msg)
            await route_message(client_id, data)

    except websockets.ConnectionClosed:
        pass
    finally:
        if client_id and client_id in CLIENTS:
            del CLIENTS[client_id]
            print(f"[-] {client_id} disconnected")
            await broadcast_user_list()

async def route_message(sender_id, data):
    """
    Expected message format:
    {
        "type": "relay",
        "to": "bob",
        "payload": "<encrypted or control data>"
    }
    """
    if data.get("type") != "relay":
        return

    target = data.get("to")
    payload = data.get("payload")

    if target in CLIENTS:
        await CLIENTS[target].send(json.dumps({
            "type": "relay",
            "from": sender_id,
            "payload": payload
        }))

async def broadcast_user_list():
    users = list(CLIENTS.keys())
    msg = json.dumps({
        "type": "users",
        "users": users
    })
    for ws in CLIENTS.values():
        await ws.send(msg)

async def main():
    print("[*] DARC signaling server running on port 8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
