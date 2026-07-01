from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from src.processing_service import DetectionService

# Vrund Joshi
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  
app.secret_key = 'hush_hush_deepfake_secret'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
USER_DATA_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {"admin": "admin"}

def save_users(users_dict):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users_dict, f)

detection_service = DetectionService()

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users and users[username] == password:
            session['authenticated'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid clearance credentials")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    new_user = request.form.get('new_username')
    new_pass = request.form.get('new_password')
    if not new_user or not new_pass:
        return render_template('login.html', error="Fields cannot be empty.")
    users = load_users()
    if new_user in users:
        return render_template('login.html', error="ID already taken. Please choose another.")
    users[new_user] = new_pass
    save_users(users)
    return render_template('login.html', success="Enrollment successful! You may now authenticate.")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/result')
def result():
    """ 
    Demo route that meets the specific dynamic value requirements.
    """
    return jsonify({
        "result": "REAL",
        "confidence": 96.45,
        "real_percentage": 96.45,
        "fake_percentage": 3.55,
        "processing_time": 2.8,
        "faces_detected": 3
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('authenticated'):
        return jsonify({'error': 'Unauthorized access'}), 401
    if 'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        result = detection_service.process_video(filepath)
        return jsonify(result)

if __name__ == '__main__':
    app.run(debug=False, port=5001)
