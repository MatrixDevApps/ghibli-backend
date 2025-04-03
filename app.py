from flask import Flask, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Allow file uploads to the "uploads" folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

@app.route('/')
def home():
    return "✅ Ghibli AI Flask Server is running!"

@app.route('/transform', methods=['POST'])
def transform_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file found"}), 400

    image = request.files['image']
    filename = secure_filename(image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    with open(filepath, "rb") as img_file:
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {REPLICATE_API_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "version": "f370727477aa04d12d8c0b5c4e3a22399296c21cd18ff67cd7619710630fe3cb",
                "input": {
                    "image": f"data:image/jpeg;base64,{img_file.read().decode('latin1')}"
                }
            }
        )

    if response.status_code != 201:
        print("🟥 Replicate Error:", response.text)
        return jsonify({"error": "Replicate API failed"}), 500

    prediction = response.json()
    return jsonify(prediction)

# ✅ Fix for Render: use 0.0.0.0 and dynamic port
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

