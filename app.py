import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load your .env variables (Replicate token)
load_dotenv()
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Initialize Flask
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs("uploads", exist_ok=True)

# Home route for testing
@app.route('/')
def hello():
    return '✅ Ghibli AI Flask Server is running!'

# Ghibli transformation route
@app.route('/transform', methods=['POST'])
def transform():
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        # Save the uploaded image
        image = request.files['image']
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        # Send a request to Replicate (prompt only for now)
        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json",
        }

        json_data = {
           "version": "f370727477aa04d12d8c0b5c4e3a22399296c21cd18ff67cd7619710630fe3cb",
  # Ghibli-style SD 1.5
            "input": {
                "prompt": "A magical Studio Ghibli anime scene with soft lighting, detailed background, whimsical forest, cinematic style"
            }
        }

        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=json_data
        )

        if response.status_code != 201:
            print("🟥 Replicate Error:", response.text)
            return jsonify({'error': response.json()}), 500

        prediction = response.json()
        return jsonify(prediction)

    except Exception as e:
        print("🟥 Server Error:", str(e))
        return jsonify({'error': str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
