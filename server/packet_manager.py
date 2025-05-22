import asyncio
import logging
from server.chunk_manager import split_chunks
from server.integrity_checker import calculate_checksum
import hashlib

logger = logging.getLogger(__name__)

async def receive_file(reader, writer, dest_path):
    file_size = int.from_bytes(await reader.readexactly(8), 'big')
    received = 0
    expected_seq = 0

    with open(dest_path, 'wb') as f:
        while received < file_size:
            seq_num = int.from_bytes(await reader.readexactly(4), 'big')
            chunk_size = int.from_bytes(await reader.readexactly(4), 'big')
            chunk = await reader.readexactly(chunk_size)
            checksum = (await reader.readexactly(64)).decode()

            if calculate_checksum(chunk) != checksum:
                logger.warning(f"Checksum mismatch on chunk {seq_num}")
                await send_ack(writer, b'NACK')
                continue

            if seq_num != expected_seq:
                logger.warning(f"Out-of-order chunk {seq_num} received, expected {expected_seq}")
                await send_ack(writer, b'NACK')  
                continue

            f.write(chunk)
            received += chunk_size
            expected_seq += 1
            await send_ack(writer, b'ACKN')

async def send_ack(writer, code: bytes):
    writer.write(code)
    await writer.drain()

def calculate_file_checksum(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

async def send_file(writer, filepath, username=None):
    chunks = list(split_chunks(filepath))
    total_size = sum(len(c) for c in chunks)

    writer.write(total_size.to_bytes(8, 'big'))
    await writer.drain()

    for seq_num, chunk in enumerate(chunks):
        writer.write(seq_num.to_bytes(4, 'big'))                 # sequence number
        writer.write(len(chunk).to_bytes(4, 'big'))              # chunk size
        writer.write(chunk)                                      # chunk data
        writer.write(calculate_checksum(chunk).encode())         # checksum
        await writer.drain()

        logger.info(f"Sent chunk #{seq_num} to client '{username}': {chunk[:20]}... ({len(chunk)} bytes)")

    # Calculate and send the file-level checksum
    file_checksum = calculate_file_checksum(filepath)
    writer.write(file_checksum.encode())
    await writer.drain()
    logger.info(f"Sent file-level checksum to client '{username}': {file_checksum}")