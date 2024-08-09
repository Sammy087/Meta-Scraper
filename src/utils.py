import os
import time
import logging
import random
from moviepy.editor import VideoFileClip, ColorClip
from PIL import Image

logging.basicConfig(level=logging.INFO)

def generate_background_image(width, height):
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    background = ColorClip((width, height), color=color)
    return background

def force_close_file(filepath):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with open(filepath, 'rb') as f:
                f.close()
            os.remove(filepath)
            logging.info(f"Removed file: {filepath}")
            return True
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1}/{max_retries} failed to remove file {filepath}: {e}")
            time.sleep(1)
    return False

def cleanup_temp_files():
    for temp_file in os.listdir('.'):
        if temp_file.startswith('temp'):
            force_close_file(temp_file)
