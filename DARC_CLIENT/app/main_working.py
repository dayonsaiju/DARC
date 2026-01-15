import sys
import asyncio
import threading
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QWidget, QLabel, 
                             QFrame, QVBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt
from config import SERVER_URL
from network.signaling import SignalingClient
from ui.device_list import DeviceList
from ui.chat import Chat

# Simple terminal input for name
CLIENT_ID = input("Enter your name (alice/bob): ")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_session = None
        self.current_chat = None
        self.client = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("DARC Secure Chat - Quantum Encrypted Messaging")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F0F0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Device list (left panel)
        self.device_list = DeviceList()
        main_layout.addWidget(self.device_list)
        
        # Welcome screen (right panel initially)
        self.welcome_widget = self.create_welcome_screen()
        main_layout.addWidget(self.welcome_widget, 1)
        
        self.setLayout(main_layout)
        
    def create_welcome_screen(self):
        welcome = QFrame()
        welcome.setStyleSheet("""
            QFrame {
                background-color: white;
                border-left: 1px solid #E8E8E8;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo/Icon
        icon_label = QLabel("🔐")
        icon_label.setStyleSheet("font-size: 80px; margin-bottom: 20px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome text
        title = QLabel("Welcome to DARC Secure Chat")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #075E54;
            margin-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Quantum-Encrypted Messaging")
        subtitle.setStyleSheet("""
            font-size: 16px;
            color: #666;
            margin-bottom: 30px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Instructions
        instructions = QLabel("Select a contact from the list to start chatting")
        instructions.setStyleSheet("""
            font-size: 14px;
            color: #888;
        """)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Security info
        security_label = QLabel("🛡️ End-to-end encryption with quantum key distribution")
        security_label.setStyleSheet("""
            font-size: 12px;
            color: #25D366;
            margin-top: 20px;
        """)
        security_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(instructions)
        layout.addWidget(security_label)
        
        welcome.setLayout(layout)
        return welcome
        
    def start_chat(self, target_name, session):
        # Remove welcome screen if it exists
        if self.welcome_widget and self.welcome_widget.parent():
            self.layout().removeWidget(self.welcome_widget)
            self.welcome_widget.deleteLater()
            self.welcome_widget = None
            
        # Remove existing chat if any
        if self.current_chat and self.current_chat.parent():
            self.layout().removeWidget(self.current_chat)
            self.current_chat.deleteLater()
            
        # Create new chat
        self.current_session = session
        self.current_chat = Chat(target_name, self.send_message)
        
        # Add chat to layout
        self.layout().addWidget(self.current_chat, 1)
        
        # Show welcome message
        self.current_chat.add_message(f"🔐 Secure session established with {target_name}", is_sent=True)
        self.current_chat.add_message("Messages are encrypted with quantum-derived keys", is_sent=False)
        
    def send_message(self, message):
        if self.client and self.current_session:
            asyncio.run_coroutine_threadsafe(
                self.client.send(self.current_chat.target_name, 
                               self.current_session.encrypt_message(message)),
                self.client.loop
            )
            
    def on_message_received(self, data):
        if self.current_chat:
            try:
                msg = self.current_session.decrypt_message(data["payload"])
                self.current_chat.receive_message(msg)
            except Exception as e:
                print(f"Error decrypting message: {e}")
                
    def update_users(self, users):
        self.device_list.update_users(users)

app = QApplication(sys.argv)

current_session = None
chat = None
client = None
main_window = None

def on_message(data):
    global current_session, chat, main_window
    print(f"📨 Received message: {data}")
    if data["type"] == "users":
        users = [u for u in data["users"] if u != CLIENT_ID]
        print(f"👥 Available users: {users}")
        main_window.update_users(users)
    elif data["type"] == "relay":
        main_window.on_message_received(data)

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

# Create main window
main_window = MainWindow()
main_window.device_list.device_selected.connect(main_window.start_chat)
main_window.show()

# Start asyncio in background thread
threading.Thread(target=start_async_loop, daemon=True).start()

print("🎯 DARC Client started!")
sys.exit(app.exec())
