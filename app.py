from flask import Flask, request, render_template, url_for
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv
import os

load_dotenv()
MODEL = os.getenv("IMAGE_GENERATION_MODEL")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)
client = genai.Client(vertexai=True, project=GCP_PROJECT_ID)
# client = genai.Client(api_key=GOOGLE_API_KEY)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    # Initialize URLs
    person_url = None
    apparel_url = None
    output_url = None

    if request.method == "POST":
        person_file = request.files.get("person")
        apparel_file = request.files.get("apparel")

        if not person_file or not apparel_file:
            return "Please upload both images."

        # Save uploaded files inside static/uploads
        person_path = os.path.join(UPLOAD_FOLDER, "person.png")
        apparel_path = os.path.join(UPLOAD_FOLDER, "apparel.png")
        person_file.save(person_path)
        apparel_file.save(apparel_path)

        person_img = Image.open(person_path)
        apparel_img = Image.open(apparel_path)

        # Call Gemini API to generate try-on
        prompt = "Apply the apparel onto the person realistically."
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt, person_img, apparel_img],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio="4:5",
                    image_size="2K"
                ),
            )
        )

        output_path = os.path.join(UPLOAD_FOLDER, "output.png")
        for part in response.parts:
            if image := part.as_image():
                image.save(output_path)
                break

        # Prepare URLs for template
        person_url = url_for('static', filename='uploads/person.png')
        apparel_url = url_for('static', filename='uploads/apparel.png')
        output_url = url_for('static', filename='uploads/output.png')

    return render_template(
        "index.html",
        person_url=person_url,
        apparel_url=apparel_url,
        output_url=output_url
    )


if __name__ == "__main__":
    app.run(debug=True)
