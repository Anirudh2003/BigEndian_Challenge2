import socket
import threading
import pickle
import os
import argparse
import logging
import uuid
import hashlib

parser = argparse.ArgumentParser(description="This is the Multi Threaded Socket Server!")
parser.add_argument('--ip', type=str, default=socket.gethostbyname(socket.gethostname()))
parser.add_argument('--port', type=int, default=9000)
parser.add_argument('--dir', type=str, default='./host_dir')
args = parser.parse_args()

### MACROS
MAX_RETRIES = 3

### LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s: %(message)s')
file_handler = logging.FileHandler('server.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

### PROTOCOL
HEADER = 64
PACKET = 2048
FORMAT = 'utf-8'
ADDR = (args.ip, args.port)

### MESSAGES
DISCONNECT_MESSAGE = "!DISCONNECT"
UPLOAD_FILE_MESSAGE = "!UPLOAD"
SET_USERNAME_MESSAGE = "!SET_USERNAME"
VERIFY_FILE = "!VERIFY_FILE"
RESEND_FILE = "!RESEND_FILE"
ACK_FILE = "!ACK_FILE"


### BIND SOCKET TO PORT
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
except Exception as e:
    raise SystemExit(f"Failed to bind to host: {args.ip} and port: {args.port}, because {e}")

def send(obj, conn):
    msg = pickle.dumps(obj)
    msg = bytes(f'{len(msg):<{HEADER}}', FORMAT) + msg
    conn.sendall(msg)

def hash_data(data):
    return hashlib.sha256(data).hexdigest()
    

def handle_client(conn, addr):
    logger.info(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    username = str(uuid.uuid4())

    file_buffer = {}
    retry_count = 0

    try:
        while connected:
            msg_length = conn.recv(HEADER)
            if not msg_length:
                break
            msg_len = int(msg_length.decode(FORMAT).strip())
            full_msg = b''
            while len(full_msg) < msg_len:
                full_msg += conn.recv(PACKET)

            msg = pickle.loads(full_msg)

            if isinstance(msg, str) and msg == DISCONNECT_MESSAGE:
                connected = False
                logger.info(f"[DISCONNECTED] {addr} ({username})")

            elif isinstance(msg, dict):
                msg_type = msg.get("type")

                if msg_type == SET_USERNAME_MESSAGE:
                    username = msg.get("username", username)
                    logger.info(f"[USERNAME SET] {addr} identified as '{username}'")

                elif msg_type == UPLOAD_FILE_MESSAGE:
                    filename = msg["filename"]
                    filedata = msg["filedata"]
                    filehash = msg["hash"]

                    ### Verify File
                    received_hash = hash_data(filedata)
                    if received_hash != filehash:
                        logger.warning(f"[HASH MISMATCH] {filename} from {username}. Expected {filehash}, got {received_hash}")
                        if retry_count < MAX_RETRIES:
                            send({"type": RESEND_FILE, "reason": "Hash mismatch"}, conn)
                            retry_count += 1
                        else:
                            logger.error(f"[FAILED] Max retries reached for file '{filename}'")
                    else:
                        retry_count = 0
                        user_dir = os.path.join(args.dir, username)
                        os.makedirs(user_dir, exist_ok=True)
                        filepath = os.path.join(user_dir, filename)

                        with open(filepath, 'wb') as f:
                            f.write(filedata)

                        logger.info(f"[FILE SAVED] {filename} saved to {filepath}")
                        send({"type": ACK_FILE}, conn)

    except Exception as e:
        logger.error(f"[ERROR] {addr} -> {e}")
    finally:
        conn.close()
def start():
    server.listen()
    logger.info(f"[LISTENING] Server listening on {args.ip}:{args.port}")
    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            logger.info(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        logger.info("[SERVER SHUTDOWN] Gracefully shutting down.")
        server.close()

if __name__ == "__main__":
    logger.info("[STARTING] Server is starting...")
    start()
