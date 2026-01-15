from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.client_id = None
        self.setup_ui()
        
        # Force focus and make modal
        self.setModal(True)
        self.raise_()
        self.activateWindow()
        
        # Use timer to ensure focus after dialog is shown
        QTimer.singleShot(100, self.name_input.setFocus)
        
    def setup_ui(self):
        self.setWindowTitle("DARC Secure Chat - Login")
        self.setFixedSize(450, 350)
        self.setStyleSheet("""
            QDialog {
                background-color: #F0F0F0;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo
        logo = QLabel("🔐")
        logo.setStyleSheet("font-size: 60px; margin-bottom: 20px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("DARC Secure Chat")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #075E54;
            margin-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subtitle
        subtitle = QLabel("Quantum-Encrypted Messaging")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #666;
            margin-bottom: 30px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Input frame
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        input_layout = QVBoxLayout()
        
        # Label
        label = QLabel("Enter your name:")
        label.setStyleSheet("font-size: 14px; color: #303030; margin-bottom: 10px;")
        
        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., alice, bob, or your name...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E8E8E8;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                background-color: white;
                color: #303030;
            }
            QLineEdit:focus {
                border: 2px solid #25D366;
            }
        """)
        
        # Connect signals properly
        self.name_input.returnPressed.connect(self.accept_login)
        self.name_input.textChanged.connect(self.on_text_changed)
        
        # Login button
        self.login_btn = QPushButton("Start Chatting")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                color: white;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:pressed {
                background-color: #075E54;
            }
            QPushButton:disabled {
                background-color: #CCC;
            }
        """)
        self.login_btn.clicked.connect(self.accept_login)
        
        # Initially disable button
        self.login_btn.setEnabled(False)
        
        input_layout.addWidget(label)
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.login_btn)
        input_frame.setLayout(input_layout)
        
        # Add all to main layout
        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(input_frame)
        
        self.setLayout(layout)
        
        # Debug info
        print("🔐 Login dialog created")
        
    def on_text_changed(self, text):
        """Enable/disable button based on input"""
        has_text = bool(text.strip())
        self.login_btn.setEnabled(has_text)
        print(f"📝 Text changed: '{text}' (Button enabled: {has_text})")
        
    def accept_login(self):
        name = self.name_input.text().strip()
        print(f"🔑 Login attempt with name: '{name}'")
        
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid name.")
            return
            
        self.client_id = name
        print(f"✅ Login successful: {self.client_id}")
        self.accept()
        
    def get_client_id(self):
        return self.client_id
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
