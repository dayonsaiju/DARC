import sys
import asyncio
import threading
from PyQt6.QtWidgets import QApplication
from config import SERVER_URL
from network.signaling import SignalingClient
from ui.device_list import DeviceList
from ui.chat import Chat

# Simple terminal input for name
CLIENT_ID = input("Enter your name (alice/bob): ")

app = QApplication(sys.argv)

current_session = None
chat = None
client = None

def on_message(data):
    global current_session, chat
    print(f"📨 Received message: {data}")
    if data["type"] == "users":
        users = [u for u in data["users"] if u != CLIENT_ID]
        print(f"👥 Available users: {users}")
        device_list.update_users(users)
    elif data["type"] == "relay":
        msg = current_session.decrypt_message(data["payload"])
        chat.receive(msg)

def start_chat(target, session):
    global chat, current_session
    current_session = session
    print(f"🔐 Starting chat with {target}")

    chat = Chat(lambda m:
        asyncio.run_coroutine_threadsafe(
            client.send(target, session.encrypt_message(m)),
            client.loop
        )
    )
    chat.show()

def start_async_loop():
    global client
    print("🚀 Starting asyncio loop...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = SignalingClient(CLIENT_ID, on_message)
    client.loop = loop
    try:
        loop.run_until_complete(client.connect())
        print(f"✅ Connected as {CLIENT_ID}")
        loop.run_forever()
    except Exception as e:
        print(f"❌ Connection error: {e}")

# Start asyncio in background thread
threading.Thread(target=start_async_loop, daemon=True).start()

device_list = DeviceList()
device_list.device_selected.connect(start_chat)
device_list.show()

print("🎯 DARC Client started!")
sys.exit(app.exec())
