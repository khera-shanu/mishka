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

    BATCH_SIZE = 10
    for i in range(0, len(hashes), BATCH_SIZE):
        print(f"Processing {i} to {i + BATCH_SIZE}")
        hash_batch = hashes[i:i + BATCH_SIZE]
        list_of_details = get_image_text(hash_batch)
        for details in list_of_details:
            try:
                hash = details["hash"]
                city = details["city"]
                state = details["state"]
                date = details["date"]
                db.update_image_date_place(hash, city, state, date)
                print("✅")
            except Exception as e:
                print(
                    f"Error processing image:\n {e}\n"
                )
                traceback.print_exc()
                print("Skipping this image for now")

    # print("Now Extracting Place and Date info.")
    # for h in hashes:
    #     try:
    #         text, llm_text, details = get_image_text(h)
    #         city = details["city"]
    #         state = details["state"]
    #         date = details["date"]
    #         db.update_image_date_place(h, city, state, date)
    #         print("✅")
    #     except Exception as e:
    #         print(
    #             f"Error processing image {h}:\n {e}\n"
    #             "text: {text}\nllm_text: {llm_text}\ndetails: {details}"
    #         )
    #         traceback.print_exc()
    #         print("Skipping this image for now")


if __name__ == "__main__":
    main()
