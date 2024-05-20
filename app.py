import os
from flask import Flask, render_template, request, redirect, send_file
from cryptography.fernet import Fernet
from pydub import AudioSegment

app = Flask(__name__)

# Specify the upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'

# Ensure the upload and download folders exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['DOWNLOAD_FOLDER']):
    os.makedirs(app.config['DOWNLOAD_FOLDER'])

def generate_unique_filename(filename, folder):
    base_name, extension = os.path.splitext(filename)
    count = 1
    new_filename = filename
    while os.path.exists(os.path.join(folder, new_filename)):
        new_filename = f"{base_name} ({count}){extension}"
        count += 1
    return new_filename

def encrypt_audio(input_file, output_file, key):
    with open(input_file, 'rb') as file:
        audio_data = file.read()

    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(audio_data)

    with open(output_file, 'wb') as file:
        file.write(encrypted_data)

def decrypt_audio(input_file, output_file, key):
    with open(input_file, 'rb') as file:
        encrypted_data = file.read()

    cipher = Fernet(key)
    decrypted_data = cipher.decrypt(encrypted_data)

    with open(output_file, 'wb') as file:
        file.write(decrypted_data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    input_file = request.files['input_file']
    secret_key = request.form['secret_key']

    if input_file and secret_key:
        input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], input_file.filename)
        input_file.save(input_file_path)
        output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], generate_unique_filename(input_file.filename, app.config['UPLOAD_FOLDER']))

        if input_file.filename.endswith(('.opus', '.ogg')):
            audio = AudioSegment.from_file(input_file_path)
            output_file_path = output_file_path.rsplit('.', 1)[0] + '.mp3'
            audio.export(output_file_path, format='mp3')
            os.remove(input_file_path)
        else:
            output_file_path = input_file_path

        encrypt_audio(output_file_path, output_file_path, secret_key.encode())

        return redirect('/download/' + os.path.basename(output_file_path))
    else:
        return "Please provide both audio file and secret key."

@app.route('/decrypt', methods=['POST'])
def decrypt():
    input_file = request.files['input_file']
    secret_key = request.form['secret_key']

    if input_file and secret_key:
        input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], input_file.filename)
        input_file.save(input_file_path)
        output_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], generate_unique_filename(input_file.filename, app.config['DOWNLOAD_FOLDER']))

        decrypt_audio(input_file_path, output_file_path, secret_key.encode())

        return redirect('/download/' + os.path.basename(output_file_path))
    else:
        return "Please provide both encrypted audio file and secret key."

@app.route('/download/<path:filename>')
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
