from flask import Flask, request, render_template
import asyncio
from client.client import transfer_file  # Assumed to be your custom module
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    username = request.form['username']
    files = request.files.getlist('files')
    print("Uploaded files: ", files)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handle_multiple_files(username, files))

    return "Upload complete!"

async def handle_multiple_files(username, files):
    tasks = []
    for f in files:
        # Ensure nested folders are preserved if present in f.filename
        safe_path = os.path.join('/tmp', f.filename)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        f.save(safe_path)
        tasks.append(transfer_file(username, safe_path))
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
