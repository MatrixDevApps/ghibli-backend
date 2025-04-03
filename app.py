from flask import Flask, request, jsonify
import requests
import os
import time
import base64
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Folder to store uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_VERSION_ID = "f370727477aa04d12d8c0b5c4e3a22399296c21cd18ff67cd7619710630fe3cb"  # ✅ Your model version ID

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

    # Read and encode image to base64
    with open(filepath, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Step 1: Request prediction
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "version": REPLICATE_VERSION_ID,
        "input": {
            "image": f"data:image/jpeg;base64,{image_data}"
        }
    }

    response = requests.post("https://api.replicate.com/v1/predictions", json=data, headers=headers)

    if response.status_code != 201:
        print("🟥 Replicate error:", response.text)
        return jsonify({"error": "Replicate API failed"}), 500

    prediction = response.json()
    status_url = prediction["urls"]["get"]

    # Step 2: Poll until finished
    while True:
        poll = requests.get(status_url, headers=headers)
        result = poll.json()

        if result["status"] == "succeeded":
            output_url = result["output"][0]
            return jsonify({"output": output_url})

        if result["status"] == "failed":
            return jsonify({"error": "Prediction failed"}), 500

        time.sleep(2)

# ✅ Required for Render to bind to 0.0.0.0 and dynamic port
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

