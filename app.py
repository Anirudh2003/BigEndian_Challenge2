# from flask import Flask, render_template, request, redirect, url_for, send_file, flash
# import os
# from werkzeug.utils import secure_filename
# from client.client import transfer_file
# from shared.config import STORAGE_DIR

# UPLOAD_FOLDER = os.path.join(STORAGE_DIR, "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         username = request.form['username']
#         file = request.files['file']

#         if not username or not file:
#             flash("Username and file are required")
#             return redirect(request.url)

#         filename = secure_filename(file.filename)
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)

#         try:
#             received_path = transfer_file(username, filepath)
#             return send_file(received_path, as_attachment=True)
#         except Exception as e:
#             flash(f"Transfer failed: {str(e)}")
#             return redirect(request.url)

#     return render_template('index.html')


from flask import Flask, request, render_template
import asyncio
from client.client import transfer_file  # see below
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    username = request.form['username']
    files = request.files.getlist('files')
    print("filessssssss: ",files)

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
    app.run(debug=True)
