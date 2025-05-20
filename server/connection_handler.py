import os
import asyncio
import logging
from server.chunk_manager import split_chunks
from server.integrity_checker import calculate_checksum
from server.packet_manager import receive_file, send_file
from shared.config import STORAGE_DIR

logger = logging.getLogger(__name__)

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        logger.info("Client connected.")
        
        # Read username first
        username_len = int.from_bytes(await reader.readexactly(2), 'big')
        username = (await reader.readexactly(username_len)).decode()
        logger.info(f"Client username: {username}")

        # Then read filename
        filename_size = int.from_bytes(await reader.readexactly(2), 'big')
        filename = (await reader.readexactly(filename_size)).decode()

        filepath = os.path.join(STORAGE_DIR, f'server_{username}_{filename}')
        await receive_file(reader, filepath)

        logger.info(f"Received file '{filename}' from user '{username}', sending back in chunks.")
        await send_file(writer, filepath)
        logger.info("Transfer complete.")
    except Exception as e:
        logger.error(f"Error handling client: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
