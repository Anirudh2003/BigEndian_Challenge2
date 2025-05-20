# --- file: scripts/generate_server_cert.py ---
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import os

CERT_DIR = os.path.join(os.path.dirname(__file__), '', 'certs')
os.makedirs(CERT_DIR, exist_ok=True)

CA_CERT_PATH = os.path.join(CERT_DIR, 'ca.crt')
CA_KEY_PATH = os.path.join(CERT_DIR, 'ca.key')
SERVER_KEY_PATH = os.path.join(CERT_DIR, 'server.key')
SERVER_CERT_PATH = os.path.join(CERT_DIR, 'server.crt')

# Load CA private key
with open(CA_KEY_PATH, 'rb') as f:
    ca_key = serialization.load_pem_private_key(f.read(), password=None)

# Load CA certificate
with open(CA_CERT_PATH, 'rb') as f:
    ca_cert = x509.load_pem_x509_certificate(f.read())

# Generate server private key
server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Define subject for server cert
subject = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, 'localhost'),
])

# Create server certificate signed by CA
server_cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(ca_cert.subject)
    .public_key(server_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([x509.DNSName('localhost')]),
        critical=False
    )
    .sign(ca_key, hashes.SHA256())
)

# Save server key and certificate
with open(SERVER_KEY_PATH, 'wb') as f:
    f.write(server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open(SERVER_CERT_PATH, 'wb') as f:
    f.write(server_cert.public_bytes(serialization.Encoding.PEM))

print("✅ Server certificate and key generated.")
