import sys, asyncio, json
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QWidget, QLabel, 
                             QFrame, QVBoxLayout, QSizePolicy, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from config import CLIENT_ID
from network.signaling import SignalingClient
from ui.device_list import DeviceList
from ui.chat import Chat
from ui.login_dialog import LoginDialog
from ui.session_dialog import SessionRequestDialog

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_session = None
        self.current_chat = None
        self.client = None
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        # Main window setup
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
        self.device_list = DeviceList(CLIENT_ID)
        main_layout.addWidget(self.device_list)
        
        # Welcome screen (right panel initially)
        self.welcome_widget = self.create_welcome_screen()
        main_layout.addWidget(self.welcome_widget, 1)
        
        self.setLayout(main_layout)
        
        # Connection status
        self.connection_status = "Connecting..."
        
    def show_connection_status(self, status, is_connected=False):
        """Update connection status in header"""
        self.connection_status = status
        color = "#25D366" if is_connected else "#FF6B6B"
        
        # Update device list header
        for i in range(self.device_list.layout().count()):
            widget = self.device_list.layout().itemAt(i).widget()
            if hasattr(widget, 'setStyleSheet') and 'background-color: #075E54' in widget.styleSheet():
                # Update status label in header
                for child in widget.findChildren(QLabel):
                    if '●' in child.text():
                        child.setStyleSheet(f"color: {color}; font-size: 12px; margin-left: 10px;")
                        child.setText(f"● {status}")
                        break
        
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
        
    def setup_connections(self):
        self.device_list.device_selected.connect(self.start_chat)
        self.device_list.session_request.connect(self.handle_session_request)
        
    def handle_session_request(self, target_name, request_data):
        """Handle outgoing session request"""
        if self.client:
            asyncio.create_task(
                self.client.send(target_name, json.dumps(request_data))
            )
            
    def handle_incoming_session_request(self, from_name, request_data):
        """Handle incoming session request"""
        dialog = SessionRequestDialog(from_name, request_data.get("message", ""))
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.accepted:
            # Accept the session
            session_id = request_data.get("session_id")
            session = self.device_list.session.receive_session_request(session_id, from_name)
            response = session.accept_session()
            
            if response:
                asyncio.create_task(
                    self.client.send(from_name, json.dumps(response))
                )
        
    def handle_qkd_message_response(self, response, target_name):
        """Handle QKD protocol responses"""
        if response.get("status") == "ready":
            # Session is ready, open chat
            session_id = response.get("session_id")
            qkd_session = self.device_list.session.get_session(session_id)
            if qkd_session and qkd_session.state.value == 8:  # SECURE_CHAT
                from session.session_manager import Session
                session = Session(target_name, qkd_session)
                self.start_chat(target_name, session)
        elif response.get("status") == "aborted":
            QMessageBox.warning(self, "Session Failed", 
                           f"Quantum session aborted: {response.get('reason', 'Unknown error')}")
        
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
        self.current_chat.message_sent.connect(self.on_message_sent)
        
        # Add chat to layout
        self.layout().addWidget(self.current_chat, 1)
        
        # Show welcome message
        self.current_chat.add_message(f"🔐 Secure session established with {target_name}", is_sent=True)
        self.current_chat.add_message("Messages are encrypted with quantum-derived keys", is_sent=False)
        
    def send_message(self, message):
        if self.client and self.current_session:
            asyncio.create_task(
                self.client.send(self.current_chat.target_name, 
                               self.current_session.encrypt_message(message))
            )
            
    def on_message_sent(self, message):
        # Message already added to UI in send_message
        pass
        
    def on_message_received(self, data):
        if self.current_chat:
            try:
                msg = self.current_session.decrypt_message(data["payload"])
                self.current_chat.receive_message(msg)
            except Exception as e:
                print(f"Error decrypting message: {e}")
                
    def update_users(self, users):
        self.device_list.update_users(users)

def on_message(data, main_window):
    global current_session, chat
    if data["type"] == "users":
        users = [u for u in data["users"] if u != CLIENT_ID]
        main_window.update_users(users)
        main_window.show_connection_status(f"Connected ({len(users)+1} online)", True)
    elif data["type"] == "relay":
        payload = data["payload"]
        try:
            # Try to parse as JSON (QKD protocol message)
            if isinstance(payload, str):
                payload_data = json.loads(payload)
            else:
                payload_data = payload
                
            if payload_data.get("type") == "qkd_request":
                main_window.handle_incoming_session_request(data["from"], payload_data)
            else:
                # Handle other QKD protocol messages
                response = main_window.device_list.session.handle_qkd_message(payload_data)
                if response:
                    if response.get("status") in ["ready", "aborted"]:
                        main_window.handle_qkd_message_response(response, data["from"])
                    else:
                        asyncio.create_task(
                            main_window.client.send(data["from"], json.dumps(response))
                        )
        except (json.JSONDecodeError, TypeError):
            # Regular chat message
            main_window.on_message_received(data)

async def start():
    global main_window, client, CLIENT_ID
    try:
        main_window.show_connection_status("Connecting to server...", False)
        client = SignalingClient(CLIENT_ID, lambda data: on_message(data, main_window))
        await client.connect()
        main_window.client = client
        main_window.show_connection_status("Connected", True)
        print(f"✅ Connected to signaling server as {CLIENT_ID}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        main_window.show_connection_status("Connection Failed", False)
        QMessageBox.critical(main_window, "Connection Error", 
                           f"Failed to connect to server:\n{str(e)}\n\n"
                           "Please check your internet connection and try again.")

# Create application
app = QApplication(sys.argv)

# Show login dialog first
login_dialog = LoginDialog()
if login_dialog.exec() == QDialog.DialogCode.Accepted:
    CLIENT_ID = login_dialog.get_client_id()
    
    # Create main window
    main_window = MainWindow()
    main_window.show()
    
    # Start networking
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start())
    
    # Run application
    sys.exit(app.exec())
else:
    print("Login cancelled")
    sys.exit(0)
