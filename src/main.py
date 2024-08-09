import logging
from app.app import run_app
from video_processing import clean_video, download_video
from image_processing import add_watermark_to_image
from utils import generate_background_image, force_close_file, cleanup_temp_files

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_app()
