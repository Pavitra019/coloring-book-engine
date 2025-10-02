import os
import json
from flask import Flask, request, jsonify
from google.cloud import storage
from google.cloud import aiplatform

# Third-party libraries for generation/processing
from PIL import Image, ImageDraw, ImageFont 
from fpdf import FPDF
from io import BytesIO

# --- Configuration (UPDATE THESE PLACEHOLDERS) ---
# It's best practice to set these as environment variables during deployment
# But we include fallbacks here.
GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'coloringbucket')
PROJECT_ID = os.environ.get('GCP_PROJECT', 'coloring-book-473815')
LOCATION = os.environ.get('GCP_REGION', 'us-central1')

# Initialize Flask App
app = Flask(__name__)

# Initialize clients (they pick up service account credentials automatically in Cloud Run)
try:
    storage_client = storage.Client()
    # Initialize Vertex AI SDK, required for making calls to models
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    # Print error but allow app to start; clients will fail on first call if auth is bad
    print(f"Failed to initialize Google Cloud clients: {e}")

def generate_image_and_pdf(prompt: str, user_id: str):
    """
    Simulates a long-running generation task and saves output to GCS.
    
    In a real app, this section would contain the actual calls to 
    Vertex AI image/text models (e.g., Gemini or Imagen) and complex 
    data processing.
    """
    
    # 1. --- Image Creation (Simulated long task) ---
    print(f"Starting long generation for user {user_id} with prompt: {prompt}")
    
    # Placeholder: Create a simple image using Pillow
    img = Image.new('RGB', (600, 400), color = 'blue')
    d = ImageDraw.Draw(img)
    # Using a common font available via the Dockerfile's apt-get install
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 40)
    except IOError:
        # Fallback if font is not found
        font = ImageFont.load_default() 
        print("Warning: Using default font.")

    d.text((10,10), f"Generated for: {user_id[:10]}...", fill=(255,255,0), font=font)
    d.text((10,80), f"Prompt: {prompt[:40]}...", fill=(255,255,0), font=font)

    image_buffer = BytesIO()
    img.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    
    # 2. --- PDF Creation ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="GENERATED REPORT", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Prompt: {prompt}", ln=1, align="L")
    pdf.cell(200, 10, txt=f"User ID: {user_id}", ln=1, align="L")
    
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)

    # 3. --- Save to GCS ---
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    
    # Define unique filenames
    unique_id = os.getpid() # Use process ID as part of unique name
    image_filename = f"output/{user_id}/image_{unique_id}.png"
    pdf_filename = f"output/{user_id}/report_{unique_id}.pdf"
    
    # Upload files
    bucket.blob(image_filename).upload_from_file(image_buffer, content_type='image/png')
    bucket.blob(pdf_filename).upload_from_file(pdf_buffer, content_type='application/pdf')
    
    # Create public-facing links (Note: You must ensure your bucket permissions allow public access!)
    image_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{image_filename}"
    pdf_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{pdf_filename}"
    
    print(f"Generation complete. Image saved at {image_url}")
    return image_url, pdf_url


@app.route('/generate', methods=['POST'])
def generate_endpoint():
    """Main endpoint to trigger the generation process."""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        user_id = data.get('user_id', 'anonymous') 

        if not prompt:
            return jsonify({"error": "Missing 'prompt' in request body."}), 400
        
        # Call the core generation function
        image_url, pdf_url = generate_image_and_pdf(prompt, user_id)

        return jsonify({
            "message": "Generation successfully started and results saved to GCS.",
            "image_url": image_url,
            "pdf_url": pdf_url
        }), 200

    except Exception as e:
        # Log the full exception for remote debugging
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500


# Cloud Run requires the app to listen on the port specified by the PORT env variable
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
