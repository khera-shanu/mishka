import sqlite3

from config import db_path, output_image_folder


def create_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (image_hash TEXT PRIMARY KEY, image_input_path TEXT, image_output_path TEXT, image_status TEXT, city TEXT, state TEXT, date TEXT, category_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (category_id TEXT PRIMARY KEY, category_name TEXT)''')
    conn.commit()
    conn.close()


def create_categories():
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("INSERT INTO categories (category_id, category_name) VALUES ('atta', 'atta')")
    c.execute("INSERT INTO categories (category_id, category_name) VALUES ('onion', 'onion')")
    c.execute("INSERT INTO categories (category_id, category_name) VALUES ('chawal', 'chawal')")
    c.execute("INSERT INTO categories (category_id, category_name) VALUES ('dal', 'dal')")
    conn.commit()
    conn.close()


def create_image(
    image_hash, image_input_path, image_status="TODO"
):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO images (image_hash, image_input_path, image_status) VALUES (?, ?, ?)",
        (image_hash, image_input_path, image_status),
    )
    conn.commit()
    conn.close()


def update_image_date_place(
    image_hash, city, state, date, image_status="IN_PROGRESS"
):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute(
        "UPDATE images SET city = ?, state = ?, date = ?, image_status = ? WHERE image_hash = ?",
        (city, state, date, image_status, image_hash),
    )
    conn.commit()
    conn.close()


def get_category(category_id):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("SELECT category_name FROM categories WHERE category_id = ?", (category_id,))
    category = c.fetchone()
    conn.close()
    return category[0]


def _image_tuple_to_dict(image):
    return {
        "image_hash": image[0],
        "image_input_path": image[1],
        "image_output_path": image[2],
        "image_status": image[3],
        "city": image[4],
        "state": image[5],
        "date": image[6],
        "category_id": image[7],
    }


def get_all_images_with_status(status, one=False):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("SELECT * FROM images WHERE image_status = ?", (status,))
    if one is True:
        image = c.fetchone()
        conn.close()
        return _image_tuple_to_dict(image)
    images = c.fetchall()
    conn.close()
    return [_image_tuple_to_dict(image) for image in images]


def does_image_exist(image_hash):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("SELECT * FROM images WHERE image_hash = ?", (image_hash,))
    image = c.fetchone()
    conn.close()
    return image is not None


def get_category_map():
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()
    conn.close()
    return {category[0]: category[1] for category in categories}


def get_image(image_hash):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("SELECT * FROM images WHERE image_hash = ?", (image_hash,))
    image = c.fetchone()
    conn.close()
    return _image_tuple_to_dict(image)


def finalize_image(image_hash, category_id, image_output_path, city_override=None, image_status="DONE"):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    if city_override is None:
        c.execute(
            "UPDATE images SET category_id = ?, image_output_path = ?, image_status = ? WHERE image_hash = ?",
            (category_id, image_output_path, image_status, image_hash),
        )
    else:
        c.execute(
            "UPDATE images SET category_id = ?, image_output_path = ?, image_status = ?, city = ? WHERE image_hash = ?",
            (category_id, image_output_path, image_status, city_override, image_hash),
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db()
    create_categories()
