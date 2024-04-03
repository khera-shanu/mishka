import hashlib
import base64
import traceback
import json
import os
from io import BytesIO

import easyocr
import requests
from PIL import Image

import db
from config import input_image_folder, output_image_folder
from consts import states_and_uts


def get_image_hash(image_path):
    with open(image_path, "rb") as file:
        md5_hash = hashlib.md5(file.read()).hexdigest()
        return md5_hash


def get_image_hash8(image_path):
    return get_image_hash(image_path)[:8]


def get_image_base64(image_path):
    with open(image_path, "rb") as file:
        image_base64 = base64.b64encode(file.read()).decode('utf-8')
        return image_base64


def retry(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error: {e} \n\nRetrying...")
                    print(traceback.format_exc())
            return None
        return wrapper
    return decorator


@retry(3)
def call_ollama_api(
    model,
    system,
    prompt,
    _format="json",
    stream=False,
    images=None,
    max_tokens=1024,
):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "system": system,
        "format": _format,
        "stream": stream,
        "prompt": prompt,
        "max_tokens": max_tokens,
    }
    if images:
        data["images"] = images

    response = requests.post(url, data=json.dumps(data)).json()
    return json.loads(response["response"])


def extract_text_info(text):
    system = f"""
Given a text, extract the following information:
- CompleteAddress
- City
- Pincode (If present)
- Country
- Longitude
- Latitude
- Date (in DD-MM-YYYY format)
- Time
- Timezone
"""

    prompt = f"""
Given a text extracted from a pciture taken in India with location and date information,
extract the following information in the output JSON:
- CompleteAddress
- City
- Pincode (If present)
- Country
- Longitude
- Latitude
- Date in DD-MM-YYYY format
- time in HH:MM:SS format
- timezone.

Note: Either state or union territory should be filled in, but not both.

Use your knowledge of Indian states, cities, and union territories to improve the accuracy of the extraction.
Current text content (convert hindi text to english if present):

{text}
"""

    return call_ollama_api(
        "llama2:latest",
        system,
        prompt,
        max_tokens=256,
    )


def get_bottom_x_percent(base64_image, x):
    image_data = base64.b64decode(base64_image)
    image = Image.open(BytesIO(image_data))
    width, height = image.size

    bottom_height = int(height * (x/100.0))
    crop_box = (0.2*width, height - bottom_height, width, height-20)
    cropped_image = image.crop(crop_box)

    buffered = BytesIO()
    cropped_image.save(buffered, format=image.format)
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return img_base64


def image_base64_to_text(image_base64, should_crop=False, crop_percent=30):
    if should_crop:
        image_data = base64.b64decode(
            get_bottom_x_percent(image_base64, crop_percent)
        )
    else:
        image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data))

    reader = easyocr.Reader(['en', 'hi'])
    recognized_text = []

    for tensor_tuple in reader.readtext(image):
        recognized_text.append(tensor_tuple[-2])

    return " ".join(recognized_text)


def get_image_text(image_hash):

    image = db.get_image(image_hash)
    image_base64 = get_image_base64(image["image_input_path"])

    text = image_base64_to_text(image_base64, should_crop=False, crop_percent=18)
    llm_text_original = extract_text_info(text.replace("GPS Map Camera", "").strip())
    llm_text = {}
    for key, value in llm_text_original.items():
        llm_text[key.lower().strip()] = value.strip() if isinstance(value, str) else value

    city = llm_text.get("city", "UNKNOWN")
    state = llm_text.get("state", "UNKNOWN")
    date = llm_text.get("date", "UNKNOWN")

    if city == "UNKNOWN":
        raise ValueError(f"City not found in the text: {llm_text}")
    if date == "UNKNOWN":
        raise ValueError(f"Date not found in the text: {llm_text}")

    date_parts = date.split("-")
    if len(date_parts) != 3:
        date_parts = date.split("/")

    if len(date_parts[2]) != 4 and len(date_parts[2]) == 2:
        date_parts[2] = f"20{date_parts[2]}"
    date = "-".join(date_parts)

    return text, llm_text, {
        "city": city,
        "state": state,
        "date": date,
    }


def get_all_images():
    images = []
    for root, dirs, files in os.walk(input_image_folder):
        for file in files:
            image_path = os.path.join(root, file)
            image_hash = get_image_hash(image_path)
            images.append(
                {
                    "image_hash": image_hash,
                    "image_path": image_path,
                }
            )
    return images


def images_ready_for_processing():
    images = get_all_images()
    num = 0
    hashes = []
    for image in images:
        if not db.does_image_exist(image["image_hash"]):
            db.create_image(
                image["image_hash"],
                image["image_path"],
            )
            hashes.append(image["image_hash"])
            num += 1
            if num % 100 == 0:
                print(f"Processed {num} images")
    print(f"DONE: Processed {num} images")
    return hashes
