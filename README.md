# 🔐 Secure Multi User File Transfer System


This is a **secure, SSL-enabled Mutli-Client file transfer system** with end-to-end verification using **digital certificates**. The system is built using **Flask (for frontend)**, **Python asyncio (for async transfers)**, and **certificate-based TLS authentication** to ensure secure and verified communications between client and server.

---

## 🧩 Features

- 🤵 **Multi Client** isolated over security certificates
- 🔐 **TLS/SSL Communication** using self-signed certificates
- 🧾 **Certificate-based authentication** (CA, client, and server certs)
- 📤📥 **Chunked file transfer** to support large files and resilience
- 🧮 **Checksum-based integrity verification** on each chunk and full file
- 🔁 **Two-way transfer**: client uploads, server sends back the verified file
- 🌐 **Web interface** for file uploads via Flask
- ⚙️ **Retry logic** on chunk corruption (NACK/ACK protocol)

---

## 📁 Project Structure

```
.
├── app.py                     # Server-side TLS and main asyncio server
├── client/
│   └── client.py              # Client-side file uploader and receiver
├── server/
│   ├── connection_handler.py  # Handles client connections
│   ├── chunk_manager.py       # File chunking logic
│   ├── integrity_checker.py   # Checksum, receiving/sending files
│   └── packet_manager.py      # Low-level chunk handling
|   |__ __init__.py
├── shared/
│   └── config.py              # Shared configs like STORAGE_DIR
|   |__ __init__.py
├── certs/
│   ├── ca.crt, ca.key         # Certificate Authority key pair
│   ├── server.crt, server.key # Server TLS cert and key
│   └── clients/               # Folder to store auto-generated client certs
├── templates/
│   └── index.html             # Upload form (Flask frontend)

├── app.py                     # TLS-secured asyncio server
├── server.py                  # Flask app entrypoint
└── requirements.txt
|__generate_ca.py              # To download ca ceritificates
|__generate_certs_server.py    # To generate server certificates
```

---

## 🚀 How to Run the Project

### 1. 🔧 Setup Python Environment

```bash
python -m venv venv
.\venv\Scripts\activate  # or source venv/bin/activate on Linux Distro
pip install -r requirements.txt
```

---

### 2. 🔑 Generate Certificates

Ensure you have:
- A CA certificate and key (`ca.crt` and `ca.key`)
- Server certificate and key (`server.crt` and `server.key`)
- These should reside in the `certs/` directory.

The client certificates will be generated on-the-fly during file upload.

> You can generate a CA and server cert like this (OpenSSL):
```bash
# Generate CA
python generate_ca.py

# Generate Server cert
python generate_certs_server.py
```

---

### 3. ▶️ Start the Server

```bash
python -m server.server
```

This runs the secure asyncio server on port `9000`.

---

### 4. 🌐 Start the Web App (Client Uploader)

```bash
python app.py
```

This runs a Flask web server (via `waitress`) on port `5000`.

Open your browser and navigate to:

```
http://localhost:5000
```

Use the form to upload one or more files.

---

## ✅ How It Works

1. User uploads file via the web interface.
2. Flask backend saves the file and spawns an asynchronous client transfer.
3. Client connects securely to the server using TLS.
4. File is sent in chunks, each chunk is verified using a SHA256 checksum.
5. Server sends the file back after successful reception.
6. The client re-verifies the received file chunk-by-chunk and as a whole.

---

## 🛠 Tech Stack

- Python 3.10+
- Flask + Waitress
- asyncio
- cryptography
- SSL/TLS
- Custom chunking & checksum logic

---

## 📌 Notes

- All transmissions are **authenticated** (only clients with valid certs can connect).
- **File storage** is handled via a configurable path in `shared/config.py`.
- You can customize chunk size in `server/chunk_manager.py`.
- The entire pipeline was test for multiple scenarios of mutli client, file size etc
- Had implemented a basic front just to check the functionality easiy.

---

## 📙 Additional Notes

- Had an idea to deploy the server in nginx so that the load balancing can be achieved along with handling http traffic but han't done it because of screening to be conducting of the core functionality of server.
- If everything works, the server and the certificates can be hosted in nginx and a server can be made and in similar way flask server can also be hosted in a apache server or uvicorn



