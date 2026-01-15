from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QPushButton, QLabel, QLineEdit,
                             QScrollArea, QFrame, QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from session.session_manager import SessionManager


class DeviceListItem(QListWidgetItem):
    def __init__(self, device_name, is_online=True, parent_list=None):
        super().__init__()
        self.device_name = device_name
        self.is_online = is_online
        self.parent_list = parent_list
        self.setup_ui()
        
    def setup_ui(self):
        # Create custom widget for list item
        widget = QWidget()
        layout = QHBoxLayout()
        
        # Status indicator
        status_label = QLabel("●")
        status_color = "#25D366" if self.is_online else "#999999"
        status_label.setStyleSheet(f"color: {status_color}; font-size: 20px; margin-right: 10px;")
        
        # Device name
        name_label = QLabel(self.device_name)
        name_font = QFont("Arial", 14, QFont.Weight.Medium)
        name_label.setFont(name_font)
        
        # Start session button
        start_button = QPushButton("Start Chat")
        start_button.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:pressed {
                background-color: #075E54;
            }
        """)
        start_button.clicked.connect(lambda: self.on_start_session())
        
        # Online status text
        status_text = "Online" if self.is_online else "Offline"
        status_label_text = QLabel(status_text)
        status_label_text.setStyleSheet(f"color: {status_color}; font-size: 12px;")
        
        # Add to layout
        layout.addWidget(status_label)
        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(start_button)
        layout.addWidget(status_label_text)
        
        widget.setLayout(layout)
        widget.setMinimumHeight(60)
        
        # Set as item widget
        self.setSizeHint(widget.sizeHint())
        
    def on_start_session(self):
        if self.parent_list:
            self.parent_list.start_session_with_device(self.device_name)


class DeviceList(QWidget):
    device_selected = pyqtSignal(str, object)  # device_name, session
    session_request = pyqtSignal(str, dict)  # target_name, request_data
    
    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.session = SessionManager(client_id)
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Search bar
        search_bar = self.create_search_bar()
        main_layout.addWidget(search_bar)
        
        # Device list
        self.device_list = QListWidget()
        self.device_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #ECE5DD;
                outline: 0px;
            }
            QListWidget::item {
                border-bottom: 1px solid #E8E8E8;
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #DCF8C6;
            }
            QListWidget::item:hover {
                background-color: #F5F5F5;
            }
        """)
        self.device_list.itemClicked.connect(self.on_device_clicked)
        main_layout.addWidget(self.device_list)
        
        self.setLayout(main_layout)
        self.setMinimumWidth(350)
        self.setMaximumWidth(400)
        
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
        
        # Title
        title = QLabel("DARC Secure Chat")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        # Status indicator
        status = QLabel("● Connected")
        status.setStyleSheet("color: #25D366; font-size: 12px; margin-left: 10px;")
        
        layout.addWidget(title)
        layout.addWidget(status)
        layout.addStretch()
        
        header.setLayout(layout)
        return header
        
    def create_search_bar(self):
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("🔍 Search or start new chat...")
        search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E8E8E8;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
                background-color: white;
                color: #303030;
            }
            QLineEdit:focus {
                border: 2px solid #25D366;
                background-color: white;
            }
        """)
        
        layout.addWidget(search_input)
        search_frame.setLayout(layout)
        return search_frame
        
    def on_device_clicked(self, item):
        if isinstance(item, DeviceListItem):
            # Create a new session for this device
            session = self.session.create_session(item.device_name)
            self.device_selected.emit(item.device_name, session)
            
    def update_users(self, users):
        self.device_list.clear()
        for user in users:
            item = DeviceListItem(user, is_online=True, parent_list=self)
            self.device_list.addItem(item)
            
    def start_session_with_device(self, device_name):
        """Start a QKD session with the selected device"""
        # Create session and generate request
        qkd_session = self.session.create_session(device_name)
        request_data = qkd_session.generate_qkd_request()
        
        # Show session request dialog
        reply = QMessageBox.question(
            self, 
            f"Quantum Session Request",
            f"Initiate quantum-encrypted session with {device_name}?\n\n"
            f"This will establish a secure key using BB84 quantum key distribution.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.session_request.emit(device_name, request_data)
