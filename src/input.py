import base64
from openai import OpenAI
import os
from dotenv import load_dotenv
from pdf2image import convert_from_path


load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')


client = OpenAI(
  api_key=api_key)


# Step 1: Convert PDF to Images
def pdf_to_images(pdf_path, output_dir):
    
    images = convert_from_path(pdf_path)
    image_paths = []

    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"page_{i + 1}.jpg")
        image.save(image_path, "JPEG")
        image_paths.append(image_path)
    
    return image_paths
  

# Step 2: Analyze Images with OpenAI Vision
# Chat completion params https://platform.openai.com/docs/api-reference/chat/create
def analyze_images_with_openai(image_paths):
    results = []

    for image_path in image_paths:
        print(f"Processing: {image_path}")
        with open(image_path, "rb") as image_file:
      
            # Getting the base64 string
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Use OpenAI Vision to process each page  
            response = client.chat.completions.create(
              model="gpt-4o-mini",
              messages=[
                {
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": "Transcribe this image with the following in mind: as I will be using this document for RAG, please label when to chunk the text by: CHUNK_HERE. Keep in mind that the text can bleed over into another photo that you won't see in this iteration, as such chunk it accordingly. Additionally describe any images you see on the document. Please avoid transcribing watermarks. Do not reply with anything besides transcribed text, just follow the instructions.",
                    },
                    {
                      "type": "image_url",
                      "image_url": {
                        "url":  f"data:image/jpeg;base64,{base64_image}"
                      },
                    },
                  ],
                }
              ],
            )
            results.append(response)
            # print(response.choices[0].message.content)

    return results


# Define directories
pdf_path = "example.pdf"
output_dir = "./images"
os.makedirs(output_dir, exist_ok=True)

# Run the functions. Keep in mind this may take awhile and be moderately expensive:
# rule of thumb: - ~$0.004011 per page
#                - ~9 seconds per page

image_paths = pdf_to_images(pdf_path, output_dir)
doc = analyze_images_with_openai(image_paths)

md_file_name = "example.txt" # Change this if you want

with open(md_file_name, 'a') as f:
    for page in range(len(doc)):
        f.write(doc[page].choices[0].message.content + '\n\n')