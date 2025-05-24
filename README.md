# DID WBA Client and Server Example

> **中文版本**: [README_cn.md](README_cn.md)

This is a DID WBA method example implemented using FastAPI and Agent_Connect library, supporting both client and server functionality.

For detailed technical documentation, please refer to [Technical Documentation](/doc/technical_documentation_en.md)

## Features

### Server Features
- Supports DID WBA authentication protocol
- Implements two types of authentication:
  - DID WBA initial authentication
  - Bearer Token authentication
- Provides ad.json endpoint with authentication

### Client Features
- Automatically generates DID documents and private keys, or loads existing DIDs
- Initiates DID WBA authentication requests to the server
- Receives and processes access tokens
- Uses tokens for subsequent requests

## Installation

### Environment Setup

1. Clone the project
2. Create environment configuration file
   ```
   cp .env.example .env
   ```
3. Edit the .env file and set necessary configuration items

### Install Dependencies with Poetry

```bash
# Create virtual environment and install dependencies with Poetry
poetry install

# Activate virtual environment
poetry shell

# Or activate virtual environment this way (if it already exists)
source .venv/bin/activate
```

## Running the Example

### Important Note: Start the Server First, Then the Client

To see the complete interaction, you must first start a server mode, then start the client mode. This is because the client needs to connect to a running server for authentication and interaction.

#### Step 1: Start the Server

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Start server in the first terminal window
python did_server.py
```

#### Step 2: Start the Client

```bash
# Start client in the second terminal window, specifying a different port
python did_server.py --client --port 8001
```

#### Other Command Options

```bash
# Run server on specific port
python did_server.py --port 8001

# Run client with specific id
python did_server.py --client --unique-id your_unique_id
```

The server will start on the specified port (default 8000), and you can access the API documentation at `http://localhost:8000/docs`.

## API Endpoints

- `GET /agents/example/ad.json`: Get agent description information
- `GET /ad.json`: Get advertisement JSON data, requires authentication
- `POST /auth/did-wba`: DID WBA initial authentication
- `GET /auth/verify`: Verify Bearer Token
- `GET /wba/test`: Test DID WBA authentication
- `GET /wba/user/{user_id}/did.json`: Get user DID document
- `PUT /wba/user/{user_id}/did.json`: Save user DID document

## Workflow

### Server Workflow
1. Start server and listen for requests
2. Receive DID WBA authentication requests and verify signatures
3. Generate and return access tokens
4. Handle subsequent requests using tokens

### Client Workflow
1. Generate or load DID documents and private keys
2. Send requests with DID WBA signature headers to the server
3. Receive and save tokens
4. Use tokens for subsequent requests

## Authentication

The example implements two authentication methods:

1. **Initial DID WBA Authentication**: Signature verification according to DID WBA specification
2. **Bearer Token Authentication**: Subsequent request authentication through JWT tokens

For detailed authentication flow, please refer to the code implementation and [DID WBA Specification](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/chinese/03-did%3Awba%E6%96%B9%E6%B3%95%E8%A7%84%E8%8C%83.md) 