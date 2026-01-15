import uuid
from crypto.qkd_session import QKDSession, QKDState

class SessionManager:
    def __init__(self, client_id):
        self.client_id = client_id
        self.sessions = {}
        self.pending_requests = {}
        
    def create_session(self, target_name):
        """Create a new QKD session with target device"""
        session_id = str(uuid.uuid4())
        session = QKDSession(session_id, target_name, is_initiator=True)
        self.sessions[session_id] = session
        return session
        
    def receive_session_request(self, session_id, from_name):
        """Handle incoming session request"""
        session = QKDSession(session_id, from_name, is_initiator=False)
        self.sessions[session_id] = session
        self.pending_requests[session_id] = session
        return session
        
    def get_session(self, session_id):
        """Get existing session by ID"""
        return self.sessions.get(session_id)
        
    def handle_qkd_message(self, message_data):
        """Handle QKD protocol messages"""
        session_id = message_data.get("session_id")
        msg_type = message_data.get("type")
        session = self.get_session(session_id)
        
        if not session:
            return None
            
        if msg_type == "qkd_request":
            return session.accept_session()
            
        elif msg_type == "qkd_states":
            return session.receive_qkd_states(message_data["states"])
            
        elif msg_type == "basis_exchange":
            return session.receive_bases(message_data["bases"])
            
        elif msg_type == "qber_sample":
            return session.receive_qber_sample(
                message_data["sample_indices"], 
                message_data["sample_bits"]
            )
            
        elif msg_type == "key_confirmation":
            return session.receive_key_confirmation(message_data["confirmation"])
            
        elif msg_type == "session_ready":
            return {"status": "ready", "session_id": session_id}
            
        elif msg_type == "qkd_abort" or msg_type == "key_mismatch":
            session.terminate_session()
            return {"status": "aborted", "reason": message_data.get("reason", "Key mismatch")}
            
        return None

class Session:
    def __init__(self, target_name, session):
        self.target_name = target_name
        self.qkd_session = session

    def encrypt_message(self, msg):
        return self.qkd_session.encrypt_message(msg)

    def decrypt_message(self, data):
        return self.qkd_session.decrypt_message(data)
