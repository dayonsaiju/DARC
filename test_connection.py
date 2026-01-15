import asyncio
import json
import websockets

async def test_client(client_id):
    uri = "ws://localhost:8765"
    try:
        print(f"[{client_id}] Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print(f"[{client_id}] Connected!")
            
            # Register
            await websocket.send(json.dumps({
                "type": "register",
                "client_id": client_id
            }))
            print(f"[{client_id}] Sent registration")
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                print(f"[{client_id}] Received: {data}")
                
                if data.get("type") == "users":
                    users = data.get("users", [])
                    other_users = [u for u in users if u != client_id]
                    print(f"[{client_id}] Other users: {other_users}")
                    
    except Exception as e:
        print(f"[{client_id}] Error: {e}")

async def main():
    print("🧪 Testing WebSocket connections...")
    
    # Start Alice
    alice_task = asyncio.create_task(test_client("alice"))
    
    # Wait a bit
    await asyncio.sleep(1)
    
    # Start Bob
    bob_task = asyncio.create_task(test_client("bob"))
    
    # Wait for both
    await asyncio.gather(alice_task, bob_task)

if __name__ == "__main__":
    asyncio.run(main())
