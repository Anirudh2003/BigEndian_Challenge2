import socket
import pickle
import os
import hashlib

HEADER = 64
CHUNK_SIZE = 2048
FORMAT = 'utf-8'
SERVER_IP = socket.gethostbyname(socket.gethostname())
PORT = 9000
ADDR = (SERVER_IP, PORT)

UPLOAD_FILE = "!UPLOAD"
SEND_CHUNK = "!SEND_CHUNK"
RETRANSMIT_CHUNK = "!RETRANSMIT_CHUNK"
END_TRANSMISSION = "!DONE"

def hash_data(data):
    return hashlib.sha256(data).hexdigest()

def send(sock, obj):
    msg = pickle.dumps(obj)
    msg = bytes(f"{len(msg):<{HEADER}}", FORMAT) + msg
    sock.sendall(msg)

def receive(sock):
    try:
        msg_len = sock.recv(HEADER)
        if not msg_len:
            return None
        total_len = int(msg_len.decode(FORMAT).strip())
        full_msg = b''
        while len(full_msg) < total_len:
            packet = sock.recv(min(CHUNK_SIZE, total_len - len(full_msg)))
            if not packet:
                return None
            full_msg += packet
        return pickle.loads(full_msg)
    except Exception as e:
        print(f"[ERROR] Receiving: {e}")
        return None

def send_file(client, filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    send(client, {
        "type": UPLOAD_FILE,
        "filename": os.path.basename(filepath),
        "data": data
    })

    received_chunks = {}
    total_chunks = None

    while True:
        msg = receive(client)
        if not msg:
            break

        if msg.get("type") == SEND_CHUNK:
            idx = msg["index"]
            chunk_data = msg["data"]
            expected_hash = msg["hash"]
            total_chunks = msg["total"]

            if hash_data(chunk_data) != expected_hash:
                print(f"[HASH MISMATCH] Chunk {idx}. Requesting retransmit.")
                send(client, {
                    "type": RETRANSMIT_CHUNK,
                    "index": idx
                })
            else:
                print(f"[RECEIVED] Chunk {idx} OK.")
                received_chunks[idx] = chunk_data
                send(client, {
                    "type": "ACK",
                    "index": idx
                })

            if len(received_chunks) == total_chunks:
                break

    send(client, {"type": END_TRANSMISSION})
    print(f"[INFO] All {len(received_chunks)} chunks received. Reassembling file...")

    with open("received_from_server_file", 'wb') as f:
        for i in sorted(received_chunks):
            f.write(received_chunks[i])

    print("[SUCCESS] File reconstructed as 'received_from_server_file'")

def main():
    filepath = input("Enter file path to send: ").strip()
    if not os.path.isfile(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    print(f"[CONNECTED] Connected to {ADDR}")

    send_file(client, filepath)
    client.close()
    print("[DISCONNECTED]")

if __name__ == "__main__":
    main()
