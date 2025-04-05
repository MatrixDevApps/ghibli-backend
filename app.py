import os
import time
import requests
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

@app.route("/")
def home():
    return "Ghibli AI Backend is running."

@app.route("/transform", methods=["POST"])
def transform():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files["image"]
    image_path = os.path.join(tempfile.gettempdir(), image_file.filename)
    image_file.save(image_path)

    # Upload image to Replicate's image hosting
    with open(image_path, "rb") as f:
        response = requests.post(
            "https://dreambooth-api-experimental.replicate.com/v1/upload",
            headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"},
            files={"file": f}
        )

    if response.status_code != 200:
        return jsonify({"error": "Failed to upload image"}), 500

    uploaded_url = response.json()["url"]

    # Call the model prediction endpoint
    prediction_response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "version": "b14b9bd24838e30f8c7725437ed297907d50d91d9a61b6c07dc2d0c8d8e6bdfb",
            "input": {
                "image": uploaded_url,
                "prompt": "Studio Ghibli style, highly detailed, whimsical scenery",
                "scheduler": "K_EULER_ANCESTRAL",
                "num_outputs": 1,
                "guidance_scale": 3.5
            }
        },
    )

    if prediction_response.status_code != 201:
        return jsonify({"error": "Failed to create prediction"}), 500

    prediction = prediction_response.json()
    status_url = prediction["urls"]["get"]

    # Poll for completion
    while True:
        poll = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"})
        result = poll.json()

        if result["status"] == "succeeded":
            output_url = result["output"][0]

            image_response = requests.get(output_url)
            if image_response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp_file.write(image_response.content)
                temp_file.close()
                return send_file(temp_file.name, mimetype='image/jpeg')
            else:
                return jsonify({"error": "Failed to download image"}), 500

        if result["status"] == "failed":
            return jsonify({"error": "Prediction failed"}), 500

        time.sleep(2)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

