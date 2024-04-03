import os

input_image_folder = os.path.join(os.path.expanduser("~"), "Desktop", "input_images")
output_image_folder = os.path.join(os.path.expanduser("~"), "Desktop", "output_images")

db_path = os.path.join(os.path.dirname(__file__), "files.db")

GRID_SIZE = 3

AI_URL = "http://ubuntu@ec2-54-82-8-87.compute-1.amazonaws.com:9191/mohit-ai"
