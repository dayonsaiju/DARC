import sys
import asyncio
import threading
from PyQt6.QtWidgets import QApplication
from config import SERVER_URL
from network.signaling import SignalingClient
from ui.device_list import DeviceList
from ui.chat import Chat

CLIENT_ID = input("Enter your name (alice/bob): ")

app = QApplication(sys.argv)

current_session = None
chat = None
client = None

def on_message(data):
    global current_session, chat
    if data["type"] == "users":
        device_list.update_users(
            [u for u in data["users"] if u != CLIENT_ID]
        )

    elif data["type"] == "relay":
        msg = current_session.decrypt_message(data["payload"])
        chat.receive(msg)

def start_chat(target, session):
    global chat, current_session
    current_session = session

    chat = Chat(lambda m:
        asyncio.run_coroutine_threadsafe(
            client.send(target, session.encrypt_message(m)),
            client.loop
        )
    )
    chat.show()

def start_async_loop():
    global client
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = SignalingClient(CLIENT_ID, on_message)
    client.loop = loop
    loop.run_until_complete(client.connect())
    loop.run_forever()

# Start asyncio in background thread
threading.Thread(target=start_async_loop, daemon=True).start()

device_list = DeviceList(start_chat)
device_list.show()

sys.exit(app.exec())
