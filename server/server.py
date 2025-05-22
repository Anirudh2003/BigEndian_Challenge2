import asyncio
import ssl
import logging
from server.connection_handler import handle_client

HOST = '0.0.0.0'
PORT = 9000
SERVER_CERT = 'certs/server.crt'
SERVER_KEY = 'certs/server.key'
CA_CERT = 'certs/ca.crt'

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def create_ssl_context():
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    ssl_ctx.load_verify_locations(CA_CERT)
    return ssl_ctx

async def main():
    ssl_ctx = create_ssl_context()
    server = await asyncio.start_server(handle_client, HOST, PORT, ssl=ssl_ctx)
    addr = server.sockets[0].getsockname()
    logger.info(f'Serving on {addr}')
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
