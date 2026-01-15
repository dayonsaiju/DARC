import asyncio
import json
import websockets
from config import SERVER_URL
from session.quantum_session import QuantumSession, SessionState

class QuantumSignalingClient:
    """Enhanced signaling client for quantum communication"""
    
    def __init__(self, client_id, on_message):
        self.client_id = client_id
        self.on_message = on_message
        self.ws = None
        self.sessions = {}  # peer_id -> QuantumSession
        self.connected_users = []
        
    async def connect(self):
        """Connect to signaling server"""
        try:
            self.ws = await websockets.connect(SERVER_URL)
            await self.ws.send(json.dumps({
                "type": "register",
                "client_id": self.client_id
            }))
            asyncio.create_task(self.listen())
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def listen(self):
        """Listen for incoming messages"""
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                await self.handle_message(data)
        except websockets.ConnectionClosed:
            print("Disconnected from server")
        except Exception as e:
            print(f"Listen error: {e}")
    
    async def handle_message(self, data):
        """Handle incoming messages"""
        msg_type = data.get("type")
        
        if msg_type == "users":
            self.connected_users = [u for u in data["users"] if u != self.client_id]
            self.on_message(data)
            
        elif msg_type == "relay":
            await self.handle_relay_message(data)
            
        elif msg_type == "session_request":
            await self.handle_session_request(data)
            
        elif msg_type == "session_accept":
            await self.handle_session_accept(data)
            
        elif msg_type == "session_restart":
            await self.handle_session_restart(data)
            
        elif msg_type == "session_terminated":
            await self.handle_session_terminated(data)
            
        elif msg_type == "qkd_qubits":
            await self.handle_qkd_qubits(data)
            
        elif msg_type == "qkd_bases":
            await self.handle_qkd_bases(data)
            
        elif msg_type == "qkd_measurements":
            await self.handle_qkd_measurements(data)
            
        elif msg_type == "key_verification":
            await self.handle_key_verification(data)
            
        elif msg_type == "key_confirmed":
            await self.handle_key_confirmed(data)
    
    async def handle_relay_message(self, data):
        """Handle encrypted chat message"""
        sender = data.get("from")
        payload = data.get("payload")
        
        if sender in self.sessions:
            session = self.sessions[sender]
            decrypted_message = session.decrypt_message(payload)
            
            if decrypted_message:
                # Increment counter for this session
                session.increment_message_counter()
                
                # Forward to UI
                self.on_message({
                    "type": "chat_message",
                    "from": sender,
                    "message": decrypted_message
                })
    
    async def handle_session_request(self, data):
        """Handle incoming session request"""
        sender = data.get("from")
        
        if sender not in self.sessions:
            # Create new session
            session = QuantumSession(self.client_id, sender, self)
            self.sessions[sender] = session
            
            # Handle request
            await session.handle_session_request(data)
            
            # Notify UI
            self.on_message({
                "type": "session_request",
                "from": sender
            })
    
    async def handle_session_accept(self, data):
        """Handle session acceptance"""
        sender = data.get("from")
        
        if sender in self.sessions:
            session = self.sessions[sender]
            await session.handle_session_accept(data)
            
            # Notify UI
            self.on_message({
                "type": "session_accepted",
                "from": sender
            })
    
    async def handle_session_restart(self, data):
        """Handle session restart"""
        sender = data.get("from")
        
        if sender in self.sessions:
            session = self.sessions[sender]
            await session.handle_session_request(data)
        else:
            # Create new session for restart
            session = QuantumSession(self.client_id, sender, self)
            self.sessions[sender] = session
            await session.handle_session_request(data)
    
    async def handle_session_terminated(self, data):
        """Handle session termination"""
        sender = data.get("from")
        
        if sender in self.sessions:
            del self.sessions[sender]
            
            # Notify UI
            self.on_message({
                "type": "session_terminated",
                "from": sender
            })
    
    async def handle_qkd_qubits(self, data):
        """Handle QKD qubits"""
        sender = data.get("from")
        
        if sender in self.sessions:
            session = self.sessions[sender]
            await session.handle_qkd_qubits(data)
    
    async def handle_qkd_bases(self, data):
        """Handle QKD bases"""
        sender = data.get("from")
        
        if sender in self.sessions:
            session = self.sessions[sender]
            await session.handle_qkd_bases(data)
    
    async def handle_qkd_measurements(self, data):
        """Handle QKD measurements"""
        sender = data.get("from")
        
        if sender in self.sessions:
            session = self.sessions[sender]
            await session.handle_qkd_measurements(data)
    
    async def handle_key_verification(self, data):
        """Handle key verification"""
        sender = data.get("from")
        
        if sender in self.sessions:
            session = self.sessions[sender]
            await session.handle_key_verification(data)
    
    async def handle_key_confirmed(self, data):
        """Handle key confirmation"""
        sender = data.get("from")
        
        if sender in self.sessions:
            session = self.sessions[sender]
            await session.handle_key_confirmed(data)
            
            # Notify UI that session is ready
            self.on_message({
                "type": "session_ready",
                "from": sender
            })
    
    async def send_session_request(self, peer_id, data):
        """Send session request"""
        await self.ws.send(json.dumps(data))
    
    async def send_session_response(self, peer_id, data):
        """Send session response"""
        await self.ws.send(json.dumps(data))
    
    async def send_qkd_data(self, peer_id, data):
        """Send QKD data"""
        await self.ws.send(json.dumps(data))
    
    async def send_message(self, peer_id, message):
        """Send encrypted message"""
        if peer_id in self.sessions:
            session = self.sessions[peer_id]
            
            if session.state == SessionState.SESSION_ACTIVE:
                # Encrypt message
                encrypted_data = session.encrypt_message(message)
                
                if encrypted_data:
                    # Send through signaling server
                    await self.ws.send(json.dumps({
                        "type": "relay",
                        "to": peer_id,
                        "payload": encrypted_data
                    }))
                    
                    # Increment counter
                    session.increment_message_counter()
                    return True
                else:
                    print("Failed to encrypt message")
                    return False
            else:
                print("Session not active for encryption")
                return False
        else:
            print("No session exists with peer")
            return False
    
    async def start_quantum_session(self, peer_id):
        """Start a quantum session with peer"""
        if peer_id not in self.sessions:
            session = QuantumSession(self.client_id, peer_id, self)
            self.sessions[peer_id] = session
        
        return await self.sessions[peer_id].start_session()
    
    async def terminate_session(self, peer_id):
        """Terminate quantum session"""
        if peer_id in self.sessions:
            await self.sessions[peer_id].terminate_session()
            del self.sessions[peer_id]
    
    def get_session_state(self, peer_id):
        """Get session state"""
        if peer_id in self.sessions:
            return self.sessions[peer_id].state
        return None
    
    def get_connected_users(self):
        """Get list of connected users"""
        return self.connected_users
