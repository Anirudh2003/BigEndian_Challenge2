import asyncio
import logging
from server.chunk_manager import split_chunks
from server.integrity_checker import calculate_checksum

logger = logging.getLogger(__name__)

async def receive_file(reader, dest_path):
    file_size = int.from_bytes(await reader.readexactly(8), 'big')
    received = 0
    with open(dest_path, 'wb') as f:
        while received < file_size:
            chunk_size = int.from_bytes(await reader.readexactly(4), 'big')
            chunk = await reader.readexactly(chunk_size)
            checksum = (await reader.readexactly(64)).decode()
            if calculate_checksum(chunk) != checksum:
                logger.warning("Checksum mismatch during upload!")
                raise ValueError("Checksum mismatch!")
            f.write(chunk)
            received += chunk_size

async def send_file(writer, filepath):
    chunks = list(split_chunks(filepath))
    total_size = sum(len(c) for c in chunks)
    writer.write(total_size.to_bytes(8, 'big'))
    await writer.drain()

    for chunk in chunks:
        writer.write(len(chunk).to_bytes(4, 'big'))
        writer.write(chunk)
        writer.write(calculate_checksum(chunk).encode())
        await writer.drain()