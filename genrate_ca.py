# utils/generate_ca.py
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime
import os

def generate_ca(ca_dir="certs"):
    os.makedirs(ca_dir, exist_ok=True)

    # Generate CA key
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with open(f"{ca_dir}/ca.key", "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))

    # Generate CA certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MyApp CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "MyApp Root CA"),
    ])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(key, hashes.SHA256())

    with open(f"{ca_dir}/ca.crt", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("[INFO] CA cert and key created.")

if __name__ == "__main__":
    generate_ca()
