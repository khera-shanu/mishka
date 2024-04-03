import os
import traceback

import db
from utils import images_ready_for_processing, get_image_text


def main():
    if not os.path.exists("files.db"):
        print("Creating the database")
        db.create_db()
        db.create_categories()

    hashes = images_ready_for_processing()
    if len(hashes) == 0:
        images = db.get_all_images_with_status("TODO")
        hashes = [image["image_hash"] for image in images]

    print("Now Extracting Place and Date info.")
    for h in hashes:
        try:
            text, llm_text, details = get_image_text(h)
            city = details["city"]
            state = details["state"]
            date = details["date"]
            db.update_image_date_place(h, city, state, date)
            print("✅")
        except Exception as e:
            print(
                f"Error processing image {h}:\n {e}\n"
                "text: {text}\nllm_text: {llm_text}\ndetails: {details}"
            )
            traceback.print_exc()
            print("Skipping this image for now")


if __name__ == "__main__":
    main()
