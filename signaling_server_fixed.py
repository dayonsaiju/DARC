import asyncio
import json
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Stores: client_id -> websocket
CLIENTS = {}

async def handler(websocket):
    """
    Enhanced WebSocket handler for DARC signaling server
    Handles client registration, message routing, and user list broadcasting
    """
    client_id = None
    remote_addr = websocket.remote_address
    
    try:
        # First message must be registration
        raw = await websocket.recv()
        msg = json.loads(raw)
        
        logger.info(f"Received message from {remote_addr}: {msg}")

        if msg.get("type") != "register":
            logger.warning(f"Invalid registration from {remote_addr}: {msg}")
            await websocket.close()
            return

        client_id = msg["client_id"]
        
        # Check for duplicate client IDs
        if client_id in CLIENTS:
            logger.warning(f"Duplicate client ID {client_id} from {remote_addr}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Client ID '{client_id}' already exists"
            }))
            await websocket.close()
            return

        CLIENTS[client_id] = websocket
        logger.info(f"[+] {client_id} connected from {remote_addr}")
        logger.info(f"Active clients: {list(CLIENTS.keys())}")

        # Notify all clients of updated user list
        await broadcast_user_list()

        # Send welcome message to new client
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Welcome {client_id}! Connected to DARC signaling server."
        }))

        # Handle messages from this client
        async for raw_msg in websocket:
            try:
                data = json.loads(raw_msg)
                logger.info(f"Message from {client_id}: {data}")
                await route_message(client_id, data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {client_id}: {e}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")

    except websockets.ConnectionClosed as e:
        logger.info(f"Connection closed for {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error in handler for {client_id}: {e}")
    finally:
        if client_id and client_id in CLIENTS:
            del CLIENTS[client_id]
            logger.info(f"[-] {client_id} disconnected")
            logger.info(f"Remaining clients: {list(CLIENTS.keys())}")
            await broadcast_user_list()

async def route_message(sender_id, data):
    """
    Route messages between clients
    Supports relay messages and QKD protocol messages
    """
    try:
        msg_type = data.get("type")
        
        if msg_type == "relay":
            target = data.get("to")
            payload = data.get("payload")
            
            if not target:
                logger.warning(f"Relay message from {sender_id} missing target")
                return
                
            if target not in CLIENTS:
                logger.warning(f"Target {target} not found for message from {sender_id}")
                await CLIENTS[sender_id].send(json.dumps({
                    "type": "error",
                    "message": f"User {target} not found"
                }))
                return
            
            # Forward message to target
            message = {
                "type": "relay",
                "from": sender_id,
                "payload": payload
            }
            
            await CLIENTS[target].send(json.dumps(message))
            logger.info(f"Relayed message from {sender_id} to {target}")
            
        else:
            logger.warning(f"Unknown message type from {sender_id}: {msg_type}")
            
    except Exception as e:
        logger.error(f"Error routing message from {sender_id}: {e}")

async def broadcast_user_list():
    """
    Broadcast updated user list to all connected clients
    """
    try:
        users = list(CLIENTS.keys())
        msg = json.dumps({
            "type": "users",
            "users": users
        })
        
        # Send to all clients
        for client_id, ws in CLIENTS.items():
            try:
                await ws.send(msg)
            except Exception as e:
                logger.error(f"Error sending user list to {client_id}: {e}")
                
        logger.info(f"Broadcasted user list: {users}")
        
    except Exception as e:
        logger.error(f"Error broadcasting user list: {e}")

async def main():
    """
    Main server function
    """
    logger.info("Starting DARC Signaling Server")
    logger.info("Supporting complete 9-state BB84 QKD protocol")
    logger.info("WebSocket server will start on 0.0.0.0:8765")
    
    # Create WebSocket server with proper configuration
    async with websockets.serve(
        handler, 
        "0.0.0.0", 
        8765,
        ping_interval=20,
        ping_timeout=10,
        close_timeout=10
    ) as server:
        logger.info("✅ DARC signaling server running on ws://0.0.0.0:8765")
        logger.info("🔐 Ready for quantum-secure messaging")
        logger.info("📡 Waiting for client connections...")
        
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server crashed: {e}")
