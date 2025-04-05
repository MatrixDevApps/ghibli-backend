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

    try:
        image_path = os.path.join(tempfile.gettempdir(), image_file.filename)
        image_file.save(image_path)
        print(f"✅ Image saved to: {image_path}")
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return jsonify({"error": f"Failed to save image: {str(e)}"}), 500

    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                "https://dreambooth-api-experimental.replicate.com/v1/upload",
                headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"},
                files={"file": f}
            )
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.text}")
            return jsonify({"error": "Failed to upload image"}), 500

        uploaded_url = response.json()["url"]
        print(f"✅ Uploaded URL: {uploaded_url}")
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

    try:
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
            print(f"❌ Prediction creation failed: {prediction_response.text}")
            return jsonify({"error": "Failed to create prediction"}), 500

        prediction = prediction_response.json()
        status_url = prediction["urls"]["get"]
        print("⏳ Polling prediction status...")

        while True:
            poll = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"})
            result = poll.json()
            if result["status"] == "succeeded":
                output_url = result["output"][0]
                print(f"✅ Prediction succeeded: {output_url}")

                image_response = requests.get(output_url)
                if image_response.status_code == 200:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                    temp_file.write(image_response.content)
                    temp_file.close()
                    return send_file(temp_file.name, mimetype='image/jpeg')
                else:
                    print(f"❌ Image download failed: {image_response.status_code}")
                    return jsonify({"error": "Failed to download image"}), 500

            if result["status"] == "failed":
                print("❌ Prediction failed")
                return jsonify({"error": "Prediction failed"}), 500

            time.sleep(2)

    except Exception as e:
        print(f"❌ Error in prediction or polling: {e}")
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

# ✅ Ensure correct port binding for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

