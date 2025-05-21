# # --- file: client/client.py ---
# import asyncio
# import ssl
# import os
# import logging
# import argparse
# from cryptography import x509
# from cryptography.x509.oid import NameOID
# from cryptography.hazmat.primitives import hashes, serialization
# from cryptography.hazmat.primitives.asymmetric import rsa
# from datetime import datetime, timedelta
# from shared.config import STORAGE_DIR
# from server.integrity_checker import calculate_checksum

# CERT_DIR = os.path.join(os.path.dirname(__file__), '..', 'certs')
# CA_CERT = os.path.join(CERT_DIR, 'ca.crt')
# CA_KEY = os.path.join(CERT_DIR, 'ca.key')
# CLIENT_CERT_DIR = os.path.join(CERT_DIR, 'clients')

# SERVER_HOST = 'localhost'
# SERVER_PORT = 9000

# os.makedirs(CLIENT_CERT_DIR, exist_ok=True)

# logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
# logger = logging.getLogger(__name__)

# def generate_client_cert(username):
#     cert_path = os.path.join(CLIENT_CERT_DIR, f'{username}.crt')
#     key_path = os.path.join(CLIENT_CERT_DIR, f'{username}.key')

#     if os.path.exists(cert_path) and os.path.exists(key_path):
#         logger.info(f"Client cert and key for '{username}' already exist.")
#         return cert_path, key_path

#     logger.info(f"Generating new client certificate for '{username}'...")

#     # Load CA key and cert
#     with open(CA_KEY, 'rb') as f:
#         ca_private_key = serialization.load_pem_private_key(f.read(), password=None)
#     with open(CA_CERT, 'rb') as f:
#         ca_cert = x509.load_pem_x509_certificate(f.read())

#     # Generate client key
#     client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
#     client_subject = x509.Name([
#         x509.NameAttribute(NameOID.COMMON_NAME, username),
#     ])

#     client_cert = (
#         x509.CertificateBuilder()
#         .subject_name(client_subject)
#         .issuer_name(ca_cert.subject)
#         .public_key(client_key.public_key())
#         .serial_number(x509.random_serial_number())
#         .not_valid_before(datetime.utcnow())
#         .not_valid_after(datetime.utcnow() + timedelta(days=365))
#         .sign(ca_private_key, hashes.SHA256())
#     )

#     with open(cert_path, 'wb') as f:
#         f.write(client_cert.public_bytes(serialization.Encoding.PEM))

#     with open(key_path, 'wb') as f:
#         f.write(client_key.private_bytes(
#             serialization.Encoding.PEM,
#             serialization.PrivateFormat.TraditionalOpenSSL,
#             serialization.NoEncryption()
#         ))

#     logger.info(f"Client certificate for '{username}' generated.")
#     return cert_path, key_path

# async def send_file(reader, writer, filepath, username):
#     username_bytes = username.encode()
#     writer.write(len(username_bytes).to_bytes(2, 'big'))
#     writer.write(username_bytes)

#     filename = os.path.basename(filepath)
#     writer.write(len(filename).to_bytes(2, 'big'))
#     writer.write(filename.encode())

#     file_size = os.path.getsize(filepath)
#     writer.write(file_size.to_bytes(8, 'big'))

#     with open(filepath, 'rb') as f:
#         while chunk := f.read(2048):
#             while True:
#                 writer.write(len(chunk).to_bytes(4, 'big'))
#                 writer.write(chunk)
#                 writer.write(calculate_checksum(chunk).encode())
#                 await writer.drain()

#                 # Wait for ACK or NACK
#                 response = await reader.readexactly(4)
#                 if response == b'ACKN':
#                     break
#                 elif response == b'NACK':
#                     logger.warning("Server reported checksum mismatch. Resending chunk...")
#                 else:
#                     raise ValueError("Unexpected response from server")

#     logger.info("File sent to server.")

# async def receive_chunks(reader, dest_path):
#     expected_size = int.from_bytes(await reader.readexactly(8), 'big')
#     received = 0
#     count = 0
#     with open(dest_path, 'wb') as f:
#         while received < expected_size:
#             chunk_size = int.from_bytes(await reader.readexactly(4), 'big')
#             chunk = await reader.readexactly(chunk_size)
#             checksum = (await reader.readexactly(64)).decode()
#             if calculate_checksum(chunk) != checksum:
#                 logger.warning("Checksum mismatch during download!")
#                 raise ValueError("Checksum mismatch during download!")
#             f.write(chunk)
#             received += chunk_size
#             count += 1

#     logger.info(f"Received file from server. Total chunks: {count}")

# async def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--username', required=True, help='Unique username for this client')
#     parser.add_argument('--filepath', required=False, help='Path to the file to send')
#     args = parser.parse_args()

#     username = args.username
#     if args.filepath:
#         filepath = args.filepath
#     filepath = os.path.join(STORAGE_DIR, 'client_sample.txt') 
#     dest_path = os.path.join(STORAGE_DIR, f'{username}_received.txt')

#     cert_path, key_path = generate_client_cert(username)

#     ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=CA_CERT)
#     ssl_ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)

#     reader, writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT, ssl=ssl_ctx)
#     await send_file(reader, writer, filepath, username)
#     await receive_chunks(reader, dest_path)

#     writer.close()
#     await writer.wait_closed()

# if __name__ == '__main__':
#     asyncio.run(main())


# --- file: client/client.py ---
import asyncio
import ssl
import os
import logging
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from shared.config import STORAGE_DIR
from server.integrity_checker import calculate_checksum

CERT_DIR = os.path.join(os.path.dirname(__file__), '..', 'certs')
CA_CERT = os.path.join(CERT_DIR, 'ca.crt')
CA_KEY = os.path.join(CERT_DIR, 'ca.key')
CLIENT_CERT_DIR = os.path.join(CERT_DIR, 'clients')

SERVER_HOST = 'localhost'
SERVER_PORT = 9000

os.makedirs(CLIENT_CERT_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def generate_client_cert(username):
    cert_path = os.path.join(CLIENT_CERT_DIR, f'{username}.crt')
    key_path = os.path.join(CLIENT_CERT_DIR, f'{username}.key')

    if os.path.exists(cert_path) and os.path.exists(key_path):
        logger.info(f"Client cert and key for '{username}' already exist.")
        return cert_path, key_path

    logger.info(f"Generating new client certificate for '{username}'...")

    with open(CA_KEY, 'rb') as f:
        ca_private_key = serialization.load_pem_private_key(f.read(), password=None)
    with open(CA_CERT, 'rb') as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, username),
    ])

    client_cert = (
        x509.CertificateBuilder()
        .subject_name(client_subject)
        .issuer_name(ca_cert.subject)
        .public_key(client_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .sign(ca_private_key, hashes.SHA256())
    )

    with open(cert_path, 'wb') as f:
        f.write(client_cert.public_bytes(serialization.Encoding.PEM))

    with open(key_path, 'wb') as f:
        f.write(client_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption()
        ))

    logger.info(f"Client certificate for '{username}' generated.")
    return cert_path, key_path

async def send_file(reader, writer, filepath, username):
    username_bytes = username.encode()
    writer.write(len(username_bytes).to_bytes(2, 'big'))
    writer.write(username_bytes)

    filename = os.path.basename(filepath)
    writer.write(len(filename).to_bytes(2, 'big'))
    writer.write(filename.encode())

    file_size = os.path.getsize(filepath)
    writer.write(file_size.to_bytes(8, 'big'))

    with open(filepath, 'rb') as f:
        seq_num = 0
        while chunk := f.read(2048):
            attempts = 0
            max_retries = 5
            while attempts < max_retries:
                writer.write(seq_num.to_bytes(4, 'big'))         # Add sequence number
                writer.write(len(chunk).to_bytes(4, 'big'))      # Chunk size
                writer.write(chunk)                              # Data
                writer.write(calculate_checksum(chunk).encode()) # Checksum
                await writer.drain()

                response = await reader.readexactly(4)
                if response == b'ACKN':
                    break
                elif response == b'NACK':
                    attempts += 1
                    logger.warning(f"Resending chunk {seq_num} (attempt {attempts})")
                else:
                    raise ValueError("Unexpected response from server")
            else:
                raise RuntimeError(f"Failed to send chunk {seq_num} after several retries.")
            seq_num += 1

    logger.info("File sent to server.")

async def receive_chunks(reader, dest_path):
    expected_size = int.from_bytes(await reader.readexactly(8), 'big')
    received = 0
    expected_seq = 0

    with open(dest_path, 'wb') as f:
        while received < expected_size:
            seq_num = int.from_bytes(await reader.readexactly(4), 'big')       # NEW
            chunk_size = int.from_bytes(await reader.readexactly(4), 'big')    # NEW
            chunk = await reader.readexactly(chunk_size)
            checksum = (await reader.readexactly(64)).decode()

            if calculate_checksum(chunk) != checksum:
                raise ValueError(f"Checksum mismatch during download! Chunk #{seq_num}")

            if seq_num != expected_seq:
                raise ValueError(f"Out-of-order chunk received! Got #{seq_num}, expected #{expected_seq}")

            f.write(chunk)
            received += chunk_size
            expected_seq += 1

    logger.info("Received file from server.")



async def transfer_file(username, filepath):
    cert_path, key_path = generate_client_cert(username)

    ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=CA_CERT)
    ssl_ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)

    dest_path = os.path.join(STORAGE_DIR, f'{username}_{os.path.basename(filepath)}_received')

    reader, writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT, ssl=ssl_ctx)
    await send_file(reader, writer, filepath, username)
    await receive_chunks(reader, dest_path)
    writer.close()
    await writer.wait_closed()
