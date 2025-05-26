from flask import Flask, request, jsonify, send_file, session
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import gridfs
from bson.objectid import ObjectId
import io
import random
import smtplib
from email.mime.text import MIMEText
import sendgrid
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["fileuploads"]
fs = gridfs.GridFS(db)

# In-memory OTP store (for demo only)
otp_store = {}

def send_email(to_email, subject, body):
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    if not sendgrid_api_key:
        print("SendGrid API key not set in environment variables.")
        return
    sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
    from_email = "spaceshare.mlrit@gmail.com"  # Use your verified sender
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body
    )
    try:
        response = sg.send(message)
        print(f"Sent OTP email to {to_email}, status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    username = request.form.get('username')
    if not username:
        return jsonify({"error": "Username required"}), 400
    if 'file' not in request.files:
        return jsonify({"error": "Missing file"}), 400

    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        # Use the user's own database for GridFS
        user_db = mongo_client[username]
        user_fs = gridfs.GridFS(user_db)
        file_id = user_fs.put(file, filename=filename)
        return jsonify({"message": f"File uploaded to {username}'s MongoDB!", "file_id": str(file_id)})
    return jsonify({"error": "Upload failed"}), 400

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_obj = fs.find_one({"filename": filename})
    if not file_obj:
        return jsonify({"error": "File not found"}), 404
    return send_file(
        io.BytesIO(file_obj.read()),
        download_name=filename,
        as_attachment=True
    )

@app.route('/download/id/<file_id>', methods=['GET'])
def download_file_by_id(file_id):
    try:
        file_obj = fs.get(ObjectId(file_id))
    except Exception:
        return jsonify({"error": "File not found"}), 404
    return send_file(
        io.BytesIO(file_obj.read()),
        download_name=file_obj.filename,
        as_attachment=True
    )

@app.route('/download/<username>/<file_id>', methods=['GET'])
def download_file_by_user_and_id(username, file_id):
    user_db = mongo_client[username]
    user_fs = gridfs.GridFS(user_db)
    try:
        file_obj = user_fs.get(ObjectId(file_id))
    except Exception:
        return jsonify({"error": "File not found"}), 404
    return send_file(
        io.BytesIO(file_obj.read()),
        download_name=file_obj.filename,
        as_attachment=True
    )

@app.route('/delete_file/<username>/<file_id>', methods=['DELETE'])
def delete_file(username, file_id):
    user_db = mongo_client[username]
    user_fs = gridfs.GridFS(user_db)
    try:
        user_fs.delete(ObjectId(file_id))
        return jsonify({"message": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to delete file"}), 500

@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    mode = data.get("mode", "signup")  # "signup" or "login"
    if mode == "login":
        # For login, find the email associated with the username
        if not username:
            return jsonify({"error": "Username required"}), 400
        user = db.users.find_one({"username": username})
        if not user:
            return jsonify({"error": "User not found"}), 404
        email = user.get("email")
        if not email:
            return jsonify({"error": "No email associated with this user"}), 400
    else:
        # For signup, use the provided email
        if not email:
            return jsonify({"error": "Email required"}), 400

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    send_email(email, "Your OTP Code", f"Your OTP is: {otp}")
    return jsonify({"message": "OTP sent to email"}), 200

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    otp = data.get("otp")
    if not username or not password or not email or not otp:
        return jsonify({"error": "All fields and OTP required"}), 400
    if db.users.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 409
    if email not in otp_store or otp_store[email] != otp:
        return jsonify({"error": "Invalid or expired OTP"}), 401
    db.users.insert_one({
        "username": username,
        "password": password,  # In production, hash this!
        "email": email
    })
    user_db = mongo_client[username]
    dummy_id = user_db['init_collection'].insert_one({"init": True}).inserted_id
    user_db['init_collection'].delete_one({"_id": dummy_id})
    otp_store.pop(email, None)
    return jsonify({"message": "User created"}), 201

@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    otp = data.get("otp")
    if not username or not password or not otp:
        return jsonify({"error": "All fields and OTP required"}), 400
    user = db.users.find_one({"username": username, "password": password})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    email = user.get("email")
    if not email or email not in otp_store or otp_store[email] != otp:
        return jsonify({"error": "Invalid or expired OTP"}), 401
    otp_store.pop(email, None)
    return jsonify({"message": "Login successful"})

@app.route('/list_files')
def list_files():
    username = request.args.get('username')
    if not username:
        return jsonify({"files": []})
    user_db = mongo_client[username]
    user_fs = gridfs.GridFS(user_db)
    files = []
    for f in user_db.fs.files.find():
        files.append({
            "_id": str(f["_id"]),
            "filename": f["filename"],
            "uploadDate": f.get("uploadDate")
        })
    return jsonify({"files": files})

@app.route('/delete_user/<username>', methods=['DELETE'])
def delete_user(username):
    # Remove user from main users collection
    result = db.users.delete_one({"username": username})
    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404

    # Drop the user's personal database (removes all files and collections)
    mongo_client.drop_database(username)
    return jsonify({"message": f"User '{username}' and their database deleted."}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
