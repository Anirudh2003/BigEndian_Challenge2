### MODULES
import socket
from socket import timeout
import argparse
import uuid
import pickle
import os
import hashlib

### Pass Arguments to script via. Terminal
parser = argparse.ArgumentParser(description="This is the client for the multi threaded socket server!")
parser.add_argument("-n", "--name", type=str, default=str(uuid.uuid4()), help="Name of the Client")
parser.add_argument('--ip', type=str, default=socket.gethostbyname(socket.gethostname()))
parser.add_argument('--port', type=int, default=9000)
parser.add_argument('--dir', type=str, default='./downloads')
args = parser.parse_args()

### PROTOCOL
TIMEOUT_SECONDS = 10
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


def createSocket():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(TIMEOUT_SECONDS)
    client.connect(ADDR)
    return client

def send(obj, client):
    msg = pickle.dumps(obj)
    msg = bytes(f'{len(msg):<{HEADER}}', FORMAT) + msg
    client.sendall(msg)

def hash_data(data):
    return hashlib.sha256(data).hexdigest()

def read_file(filepath):
    if not os.path.isfile(filepath):
        print(f"[ERROR] File '{filepath}' not found.")
        return None, None
    with open(filepath, 'rb') as f:
        return os.path.basename(filepath), f.read()

def send_file(client, filepath):
    filename, filedata = read_file(filepath)
    if not filename or not filedata:
        return

    filehash = hash_data(filedata)
    retries = 0
    max_retries = 3

    while retries <= max_retries:
        send({
            "type": UPLOAD_FILE_MESSAGE,
            "filename": filename,
            "filedata": filedata,
            "hash": filehash
        }, client)

        # Wait for ACK or RESEND
        try:
            msg_length = client.recv(HEADER)
            msg_len = int(msg_length.decode(FORMAT).strip())
            full_msg = b''
            while len(full_msg) < msg_len:
                full_msg += client.recv(PACKET)

            resp = pickle.loads(full_msg)

            if isinstance(resp, dict):
                if resp.get("type") == ACK_FILE:
                    print(f"[SUCCESS] File '{filename}' uploaded and verified.")
                    break
                elif resp.get("type") == RESEND_FILE:
                    print(f"[RETRY] Server requested resend ({resp.get('reason')}). Attempt {retries+1}")
                    retries += 1
            else:
                print("[WARNING] Unexpected response from server.")
                retries += 1
        except Exception as e:
            print(f"[ERROR] During file send: {e}")
            retries += 1

    if retries > max_retries:
        print(f"[FAILED] Could not send '{filename}' after {max_retries} attempts.")

def run():
    client = createSocket()
    print(f"[CONNECTED] Client connected to {args.ip}")

    try:
        send({"type": SET_USERNAME_MESSAGE, "username": args.name}, client)
        filepath = input("Enter file path to upload: ").strip()
        send_file(client, filepath)
        # send(DISCONNECT_MESSAGE, client)
        # client.close()
        # print(f"[DISCONNECTED]")
    except KeyboardInterrupt:
        send(DISCONNECT_MESSAGE, client)
        print("\n[KEYBOARD INTERRUPT]")

### START
if __name__ == "__main__":
    run()
