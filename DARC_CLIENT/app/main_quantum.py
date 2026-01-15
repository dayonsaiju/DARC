import sys
import asyncio
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QListWidget, QListWidgetItem, QTextEdit, 
                             QMessageBox, QDialog, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPalette
from network.quantum_signaling import QuantumSignalingClient
from session.quantum_session import SessionState

class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DARC Quantum Chat - Login")
        self.setFixedSize(450, 250)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔐 DARC Quantum Chat")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #007BFF;
            margin: 20px;
        """)
        layout.addWidget(title)
        
        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username...")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 18px;
                border: 2px solid #DEE2E6;
                border-radius: 10px;
                font-size: 16px;
                margin: 15px;
                background-color: white;
                color: #2C3E50;
            }
            QLineEdit:focus {
                border-color: #007BFF;
            }
        """)
        layout.addWidget(self.username_input)
        
        # Login button
        login_btn = QPushButton("Connect")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 18px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                margin: 15px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        login_btn.clicked.connect(self.accept)
        layout.addWidget(login_btn)
        
        self.setLayout(layout)
    
    def get_username(self):
        return self.username_input.text().strip()

class UserListItem(QListWidgetItem):
    """Custom list item for users"""
    
    def __init__(self, username, status="offline"):
        super().__init__()
        self.username = username
        self.status = status
        self.update_display()
    
    def update_display(self, session_state=None):
        """Update display based on session state"""
        if session_state == SessionState.SESSION_ACTIVE:
            status_color = "#28A745"
            status_text = "🔒 Secure"
        elif session_state and session_state != SessionState.IDLE:
            status_color = "#FFC107"
            status_text = "🔄 Establishing"
        else:
            status_color = "#6C757D"
            status_text = "📡 Available"
        
        self.setText(f"{self.username} - {status_text}")
        self.setStyleSheet(f"""
            QListWidgetItem {{
                padding: 15px 10px;
                border-bottom: 1px solid #E9ECEF;
                color: {status_color};
                font-weight: 600;
                font-size: 14px;
            }}
            QListWidget::item:hover {{
                background-color: #F8F9FA;
            }}
        """)

class ChatWidget(QWidget):
    """Chat interface widget"""
    
    message_sent = pyqtSignal(str)
    
    def __init__(self, peer_name):
        super().__init__()
        self.peer_name = peer_name
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #007BFF;
                padding: 15px;
                border-radius: 8px;
            }
        """)
        header_layout = QHBoxLayout()
        
        peer_label = QLabel(f"🔐 {self.peer_name}")
        peer_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        header_layout.addWidget(peer_label)
        
        header.setLayout(header_layout)
        layout.addWidget(header)
        
        # Messages area
        self.messages_area = QTextEdit()
        self.messages_area.setReadOnly(True)
        self.messages_area.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                padding: 15px;
                font-size: 15px;
                border-radius: 8px;
                color: #2C3E50;
            }
        """)
        layout.addWidget(self.messages_area)
        
        # Message input
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 18px;
                border: 2px solid #DEE2E6;
                border-radius: 25px;
                font-size: 16px;
                background-color: white;
                color: #2C3E50;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #007BFF;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 18px 25px;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        self.setLayout(layout)
    
    def send_message(self):
        """Send message"""
        message = self.message_input.text().strip()
        if message:
            self.message_sent.emit(message)
            self.add_message(message, is_sent=True)
            self.message_input.clear()
    
    def add_message(self, message, is_sent=False):
        """Add message to chat"""
        if is_sent:
            msg_html = f"""
            <div style="text-align: right; margin: 5px;">
                <div style="background-color: #3498DB; color: white; 
                           padding: 10px; border-radius: 10px; 
                           display: inline-block; max-width: 70%;">
                    {message}
                </div>
            </div>
            """
        else:
            msg_html = f"""
            <div style="text-align: left; margin: 5px;">
                <div style="background-color: white; color: #2C3E50; 
                           padding: 10px; border-radius: 10px; 
                           display: inline-block; max-width: 70%; 
                           border: 1px solid #BDC3C7;">
                    {message}
                </div>
            </div>
            """
        
        self.messages_area.insertHtml(msg_html)
        self.messages_area.verticalScrollBar().setValue(
            self.messages_area.verticalScrollBar().maximum()
        )
    
    def add_status_message(self, message):
        """Add status message"""
        status_html = f"""
        <div style="text-align: center; margin: 10px;">
            <div style="background-color: #F39C12; color: white; 
                       padding: 8px; border-radius: 15px; 
                       display: inline-block; font-size: 12px;">
                {message}
            </div>
        </div>
        """
        self.messages_area.insertHtml(status_html)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.current_chat = None
        self.username = None
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup main UI"""
        self.setWindowTitle("DARC Quantum Chat")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel - Users list
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-right: 2px solid #DEE2E6;
            }
        """)
        left_panel.setMaximumWidth(350)
        
        left_layout = QVBoxLayout()
        
        # Users header
        users_header = QLabel("🔐 Connected Users")
        users_header.setStyleSheet("""
            color: #2C3E50;
            font-size: 18px;
            font-weight: bold;
            padding: 15px;
            background-color: #E9ECEF;
            border-bottom: 2px solid #DEE2E6;
        """)
        left_layout.addWidget(users_header)
        
        # Users list
        self.users_list = QListWidget()
        self.users_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: none;
                color: #2C3E50;
                font-size: 14px;
                font-weight: 500;
            }
            QListWidget::item {
                padding: 15px 10px;
                border-bottom: 1px solid #E9ECEF;
                min-height: 20px;
            }
            QListWidget::item:hover {
                background-color: #F8F9FA;
            }
            QListWidget::item:selected {
                background-color: #007BFF;
                color: white;
            }
        """)
        self.users_list.itemDoubleClicked.connect(self.start_session)
        left_layout.addWidget(self.users_list)
        
        # Session controls
        controls_layout = QVBoxLayout()
        
        self.start_session_btn = QPushButton("🔐 Start Quantum Session")
        self.start_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                margin: 8px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1E7E34;
            }
        """)
        self.start_session_btn.clicked.connect(self.start_selected_session)
        controls_layout.addWidget(self.start_session_btn)
        
        self.end_session_btn = QPushButton("🔒 End Session")
        self.end_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                margin: 8px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #A71E2A;
            }
        """)
        self.end_session_btn.clicked.connect(self.end_selected_session)
        controls_layout.addWidget(self.end_session_btn)
        
        left_layout.addLayout(controls_layout)
        left_panel.setLayout(left_layout)
        main_layout.addWidget(left_panel)
        
        # Right panel - Chat area
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
            }
        """)
        
        # Welcome screen
        self.welcome_widget = self.create_welcome_screen()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.welcome_widget)
        self.right_panel.setLayout(right_layout)
        
        main_layout.addWidget(self.right_panel, 1)
    
    def create_welcome_screen(self):
        """Create welcome screen"""
        welcome = QFrame()
        welcome.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                margin: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo
        icon = QLabel("🔐")
        icon.setStyleSheet("font-size: 80px; margin-bottom: 20px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        # Title
        title = QLabel("DARC Quantum Chat")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #2C3E50;
            margin-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Quantum-Resistant Secure Messaging")
        subtitle.setStyleSheet("""
            font-size: 16px;
            color: #7F8C8D;
            margin-bottom: 30px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Instructions
        instructions = QLabel("""
        📡 Select a user from the list
        🔐 Start a quantum session
        💬 Chat with end-to-end encryption
        """)
        instructions.setStyleSheet("""
            font-size: 14px;
            color: #34495E;
            line-height: 1.5;
        """)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        welcome.setLayout(layout)
        return welcome
    
    def setup_connections(self):
        """Setup connections"""
        pass
    
    def set_client(self, client, username):
        """Set signaling client"""
        self.client = client
        self.username = username
    
    def update_users(self, users):
        """Update users list"""
        self.users_list.clear()
        
        for user in users:
            item = UserListItem(user)
            
            # Check session state
            if self.client:
                session_state = self.client.get_session_state(user)
                item.update_display(session_state)
            
            self.users_list.addItem(item)
    
    def start_session(self, item):
        """Start session with double-clicked user"""
        username = item.text().split(" - ")[0]
        self.start_quantum_session(username)
    
    def start_selected_session(self):
        """Start session with selected user"""
        current_item = self.users_list.currentItem()
        if current_item:
            username = current_item.text().split(" - ")[0]
            self.start_quantum_session(username)
    
    def start_quantum_session(self, username):
        """Start quantum session"""
        if not self.client:
            return
        
        # Create chat widget if not exists
        if not self.current_chat or self.current_chat.peer_name != username:
            self.current_chat = ChatWidget(username)
            self.current_chat.message_sent.connect(
                lambda msg: self.send_chat_message(username, msg)
            )
            
            # Replace welcome screen
            right_layout = QVBoxLayout()
            right_layout.addWidget(self.current_chat)
            self.right_panel.setLayout(right_layout)
        
        # Add status message
        self.current_chat.add_status_message("🔄 Establishing quantum session...")
        
        # Start quantum session
        asyncio.create_task(self.client.start_quantum_session(username))
    
    def end_selected_session(self):
        """End selected session"""
        current_item = self.users_list.currentItem()
        if current_item:
            username = current_item.text().split(" - ")[0]
            self.end_quantum_session(username)
    
    def end_quantum_session(self, username):
        """End quantum session"""
        if self.client:
            asyncio.create_task(self.client.terminate_session(username))
        
        if self.current_chat:
            self.current_chat.add_status_message("🔒 Session terminated")
    
    def send_chat_message(self, username, message):
        """Send chat message"""
        if self.client:
            asyncio.create_task(self.client.send_message(username, message))
    
    def handle_message(self, data):
        """Handle incoming message"""
        msg_type = data.get("type")
        
        if msg_type == "users":
            users = [u for u in data["users"] if u != self.username]
            self.update_users(users)
            
        elif msg_type == "session_request":
            sender = data.get("from")
            QMessageBox.information(self, "Session Request", 
                                  f"{sender} wants to start a quantum session")
            self.update_users(self.client.get_connected_users())
            
        elif msg_type == "session_accepted":
            sender = data.get("from")
            if self.current_chat:
                self.current_chat.add_status_message("✅ Session accepted")
            
        elif msg_type == "session_ready":
            sender = data.get("from")
            if self.current_chat:
                self.current_chat.add_status_message("🔐 Quantum key established!")
                self.current_chat.add_status_message("💬 You can now chat securely")
            
            self.update_users(self.client.get_connected_users())
            
        elif msg_type == "chat_message":
            sender = data.get("from")
            message = data.get("message")
            
            # Create or switch to chat
            if not self.current_chat or self.current_chat.peer_name != sender:
                self.current_chat = ChatWidget(sender)
                self.current_chat.message_sent.connect(
                    lambda msg: self.send_chat_message(sender, msg)
                )
                
                right_layout = QVBoxLayout()
                right_layout.addWidget(self.current_chat)
                self.right_panel.setLayout(right_layout)
            
            self.current_chat.add_message(message, is_sent=False)
            
        elif msg_type == "session_terminated":
            sender = data.get("from")
            if self.current_chat:
                self.current_chat.add_status_message("🔒 Session terminated")
            
            self.update_users(self.client.get_connected_users())

async def start_app(main_window, username):
    """Start the application"""
    try:
        # Create signaling client
        client = QuantumSignalingClient(username, 
                                      lambda data: main_window.handle_message(data))
        
        # Connect to server
        connected = await client.connect()
        if not connected:
            QMessageBox.critical(main_window, "Connection Error", 
                               "Failed to connect to signaling server")
            return
        
        main_window.set_client(client, username)
        print(f"✅ Connected as {username}")
        
    except Exception as e:
        QMessageBox.critical(main_window, "Error", f"Failed to start: {e}")

def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Show login dialog
    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        username = login.get_username()
        if not username:
            return
        
        # Create main window
        main_window = MainWindow()
        main_window.show()
        
        # Start networking
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(start_app(main_window, username))
        
        # Run application
        sys.exit(app.exec())
    else:
        print("Login cancelled")

if __name__ == "__main__":
    main()
