from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QLabel, QFrame, QScrollArea,
                             QSizePolicy, QSplitter)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QPixmap
import datetime


class MessageBubble(QLabel):
    def __init__(self, message, is_sent=True, timestamp=None):
        super().__init__()
        self.message = message
        self.is_sent = is_sent
        self.timestamp = timestamp or datetime.datetime.now().strftime("%H:%M")
        self.setup_ui()
        
    def setup_ui(self):
        # Format message with timestamp
        formatted_text = f"{self.message}\n<span style='font-size: 10px; color: #666;'>{self.timestamp}</span>"
        self.setText(formatted_text)
        
        # Style based on sender/receiver
        if self.is_sent:
            self.setStyleSheet("""
                QLabel {
                    background-color: #DCF8C6;
                    color: #303030;
                    border-radius: 18px;
                    padding: 8px 12px;
                    margin: 2px;
                    max-width: 300px;
                    font-size: 14px;
                }
            """)
            self.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: white;
                    color: #303030;
                    border-radius: 18px;
                    padding: 8px 12px;
                    margin: 2px;
                    max-width: 300px;
                    font-size: 14px;
                }
            """)
            self.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)


class Chat(QWidget):
    message_sent = pyqtSignal(str)
    
    def __init__(self, target_name, send_fn):
        super().__init__()
        self.target_name = target_name
        self.send_fn = send_fn
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Chat header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Messages area
        messages_container = self.create_messages_area()
        main_layout.addWidget(messages_container)
        
        # Input area
        input_area = self.create_input_area()
        main_layout.addWidget(input_area)
        
        self.setLayout(main_layout)
        self.setMinimumSize(500, 600)
        
    def create_header(self):
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #075E54;
                border: none;
            }
        """)
        header.setFixedHeight(60)
        
        layout = QHBoxLayout()
        
        # Back button (optional)
        back_btn = QPushButton("←")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 20px;
                padding: 5px;
                width: 30px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Contact name
        name_label = QLabel(self.target_name)
        name_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        # Online status
        status_label = QLabel("● Online")
        status_label.setStyleSheet("color: #25D366; font-size: 12px; margin-left: 10px;")
        
        # More options button
        options_btn = QPushButton("⋮")
        options_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
                padding: 5px;
                width: 30px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        layout.addWidget(back_btn)
        layout.addWidget(name_label)
        layout.addWidget(status_label)
        layout.addStretch()
        layout.addWidget(options_btn)
        
        header.setLayout(layout)
        return header
        
    def create_messages_area(self):
        # Scroll area for messages
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ECE5DD;
            }
            QScrollBar:vertical {
                background-color: #ECE5DD;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #888;
                border-radius: 5px;
            }
        """)
        
        # Container widget for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(5)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        
        self.messages_container.setLayout(self.messages_layout)
        scroll_area.setWidget(self.messages_container)
        scroll_area.setWidgetResizable(True)
        
        return scroll_area
        
    def create_input_area(self):
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #F0F0F0;
                border-top: 1px solid #E8E8E8;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout()
        
        # Attach button
        attach_btn = QPushButton("📎")
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
                padding: 5px;
                width: 40px;
                height: 40px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        
        # Message input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCC;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
                background-color: white;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #25D366;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        # Emoji button
        emoji_btn = QPushButton("😊")
        emoji_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
                padding: 5px;
                width: 40px;
                height: 40px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        
        # Send button
        self.send_btn = QPushButton("📤")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                border: none;
                border-radius: 50%;
                font-size: 16px;
                color: white;
                width: 40px;
                height: 40px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:disabled {
                background-color: #CCC;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        layout.addWidget(attach_btn)
        layout.addWidget(self.input_field, 1)
        layout.addWidget(emoji_btn)
        layout.addWidget(self.send_btn)
        
        input_frame.setLayout(layout)
        return input_frame
        
    def send_message(self):
        message = self.input_field.text().strip()
        if message:
            self.add_message(message, is_sent=True)
            self.input_field.clear()
            self.message_sent.emit(message)
            
    def add_message(self, message, is_sent=False):
        message_bubble = MessageBubble(message, is_sent)
        
        # Align messages
        if is_sent:
            h_layout = QHBoxLayout()
            h_layout.addStretch()
            h_layout.addWidget(message_bubble)
            h_layout.addStretch()
            container = QWidget()
            container.setLayout(h_layout)
        else:
            h_layout = QHBoxLayout()
            h_layout.addStretch()
            h_layout.addWidget(message_bubble)
            h_layout.addStretch()
            container = QWidget()
            container.setLayout(h_layout)
            
        self.messages_layout.addWidget(container)
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scrollbar = scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def receive_message(self, message):
        self.add_message(message, is_sent=False)
