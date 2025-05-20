import socket
import threading
import os
import pickle
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

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def hash_data(data):
    return hashlib.sha256(data).hexdigest()

def send(conn, data):
    msg = pickle.dumps(data)
    msg = bytes(f"{len(msg):<{HEADER}}", FORMAT) + msg
    conn.sendall(msg)

def receive(conn):
    try:
        msg_len = conn.recv(HEADER)
        if not msg_len:
            return None
        msg_len = int(msg_len.decode(FORMAT).strip())
        full_msg = b''
        while len(full_msg) < msg_len:
            packet = conn.recv(min(CHUNK_SIZE, msg_len - len(full_msg)))
            if not packet:
                return None
            full_msg += packet
        return pickle.loads(full_msg)
    except:
        return None

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    try:
        msg = receive(conn)
        if msg and msg.get("type") == UPLOAD_FILE:
            filename = msg["filename"]
            data = msg["data"]
            print(f"[RECEIVED] File '{filename}' ({len(data)} bytes) from {addr}")

            # Split data into chunks
            chunks = [data[i:i+CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
            total_chunks = len(chunks)

            # Send chunks to client
            for idx, chunk in enumerate(chunks):
                send(conn, {
                    "type": SEND_CHUNK,
                    "index": idx,
                    "data": chunk,
                    "hash": hash_data(chunk),
                    "total": total_chunks
                })

            acked_chunks = set()
            while len(acked_chunks) < total_chunks:
                msg = receive(conn)
                if not msg:
                    break
                if msg.get("type") == "ACK":
                    acked_chunks.add(msg["index"])
                elif msg.get("type") == RETRANSMIT_CHUNK:
                    idx = msg["index"]
                    print(f"[RETRANSMIT] Resending chunk {idx}")
                    send(conn, {
                        "type": SEND_CHUNK,
                        "index": idx,
                        "data": chunks[idx],
                        "hash": hash_data(chunks[idx]),
                        "total": total_chunks
                    })
                elif msg.get("type") == END_TRANSMISSION:
                    print(f"[DONE] Client {addr} finished receiving.")
                    break

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr}")

def start():
    server.listen()
    print(f"[LISTENING] Server running on {SERVER_IP}:{PORT}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    print("[STARTING] Server is starting...")
    start()
