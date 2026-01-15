from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SessionRequestDialog(QDialog):
    def __init__(self, from_name, message, parent=None):
        super().__init__(parent)
        self.from_name = from_name
        self.message = message
        self.accepted = False
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Quantum Session Request")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #303030;
            }
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:pressed {
                background-color: #075E54;
            }
            QPushButton#reject {
                background-color: #DC3545;
            }
            QPushButton#reject:hover {
                background-color: #C82333;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"🔐 Session Request from {self.from_name}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #075E54; margin: 10px;")
        
        # Message
        msg_label = QLabel(self.message)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setStyleSheet("margin: 10px; color: #666;")
        
        # Security info
        security_info = QLabel("This will establish a quantum-encrypted connection using BB84 protocol")
        security_info.setWordWrap(True)
        security_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        security_info.setStyleSheet("margin: 10px; color: #25D366; font-size: 12px;")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        accept_btn = QPushButton("Accept")
        accept_btn.clicked.connect(self.accept_session)
        
        reject_btn = QPushButton("Reject")
        reject_btn.setObjectName("reject")
        reject_btn.clicked.connect(self.reject_session)
        
        button_layout.addStretch()
        button_layout.addWidget(accept_btn)
        button_layout.addWidget(reject_btn)
        button_layout.addStretch()
        
        # Add to layout
        layout.addWidget(title)
        layout.addWidget(msg_label)
        layout.addWidget(security_info)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def accept_session(self):
        self.accepted = True
        self.accept()
        
    def reject_session(self):
        self.accepted = False
        self.reject()

class QKDProgressDialog(QDialog):
    def __init__(self, target_name, parent=None):
        super().__init__(parent)
        self.target_name = target_name
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Establishing Quantum Connection")
        self.setFixedSize(450, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #303030;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"🔐 Connecting to {self.target_name}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #075E54; margin: 10px;")
        
        # Status text
        self.status_label = QLabel("Initializing quantum key distribution...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("margin: 20px; color: #666;")
        
        # Progress steps
        steps_text = QLabel("""
        📡 Session Request → ⚛️ QKD Initialization → 🔄 Basis Reconciliation
        → 🔍 QBER Check → 🛠️ Error Correction → 🔑 Key Confirmation → ✅ Ready
        """)
        steps_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        steps_text.setStyleSheet("margin: 20px; color: #888; font-size: 11px;")
        
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(steps_text)
        
        self.setLayout(layout)
        
    def update_status(self, message):
        self.status_label.setText(message)
