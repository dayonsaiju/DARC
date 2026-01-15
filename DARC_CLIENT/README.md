# DARC Client

A secure quantum-resistant communication client with end-to-end encryption.

## Features

- **Quantum Key Distribution**: BB84 protocol for quantum key exchange
- **End-to-End Encryption**: AES-GCM with quantum-derived keys
- **Secure Signaling**: WebSocket-based signaling server
- **Modern UI**: PyQt6-based user interface
- **Device Discovery**: Automatic peer detection and connection

## Architecture

```
DARC_CLIENT/
├── app/
│   ├── main.py              # Main entry point
│   ├── config.py            # Configuration settings
│   ├── ui/                  # User interface components
│   │   ├── device_list.py   # Device discovery UI
│   │   └── chat.py          # Chat interface
│   ├── network/             # Network communication
│   │   └── signaling.py     # WebSocket signaling client
│   ├── session/             # Session management
│   │   └── session_manager.py  # Cryptographic sessions
│   └── crypto/              # Cryptographic modules
│       ├── qrng.py          # Quantum random number generator
│       ├── qkd_bb84.py      # BB84 quantum key distribution
│       ├── key_derivation.py # Key derivation functions
│       └── aes_gcm.py       # AES-GCM encryption
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the signaling server (in a separate terminal):
```bash
cd ..  # Go to DARC root directory
python3 signaling_server.py
```

3. Run the client:
```bash
cd DARC_CLIENT
python3 app/main.py
```

## Usage

1. Launch the client application
2. The device list will show available peers
3. Select a device to establish a secure quantum session
4. Chat with end-to-end encryption

## Security

- **Quantum-Resistant**: Uses quantum key distribution for forward secrecy
- **Zero-Knowledge**: Server never sees plaintext or encryption keys
- **Authenticated**: All messages include authentication tags
- **Perfect Forward Secrecy**: New keys generated for each session

## Configuration

Environment variables:
- `DARC_SERVER`: WebSocket server URL (default: ws://localhost:8765)
- `DARC_CLIENT_ID`: Unique client identifier

## License

MIT License
hdgffff