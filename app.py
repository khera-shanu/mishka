import os

import shutil
from flask import Flask, request, render_template

import db
from config import input_image_folder, output_image_folder, GRID_SIZE
from utils import get_image_base64


app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html",
        categories=db.get_category_map(),
        output_image_folder=output_image_folder,
    )


@app.route("/image")
def get_image():
    image = db.get_all_images_with_status("IN_PROGRESS", one=True)
    return {
        "city": image["city"],
        "state": image["state"],
        "date": image["date"],
        "image_input_path": image["image_input_path"],
        "base64": get_image_base64(image["image_input_path"]),
        "image_hash": image["image_hash"],
    }


@app.route("/finalize", methods=["POST"])
def finalize_image():
    """
    create all neccesary folders if needed for image_output_path
    and move the image to the correct folder
    move image from input path to output path
    example input path: /home/lawliet/Desktop/input_images/WhatsApp Image 2024-03-24 at 19.24.34 (19).jpeg
    example output path: /home/lawliet/Desktop/output_images/India/dal/Kurukshetra/21-03-2024/024af9.jpeg
    """

    image_hash = request.json["image_hash"]
    category_id = request.json["category_id"]
    image_output_path = request.json["image_output_path"]
    city_override = request.json.get("city_override")

    db.finalize_image(
        image_hash, category_id, image_output_path, city_override=city_override
    )

    image_input_path = db.get_image(image_hash)["image_input_path"]
    image_output_folder = os.path.dirname(image_output_path)
    os.makedirs(image_output_folder, exist_ok=True)

    shutil.move(image_input_path, image_output_path)

    return {"success": True}


if __name__ == "__main__":
    app.run(
        port=9090,
        debug=True,
    )
