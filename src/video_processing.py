import os
import time
import logging
import random
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from yt_dlp import YoutubeDL
from utils import apply_random_rotation, adjust_video_properties, remove_metadata
import add_invisible_watermark_to_video

logging.basicConfig(level=logging.INFO)

def download_video(url, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    def progress_hook(d):
        if d['status'] == 'finished':
            print(f"Done downloading video: {d['filename']}")

    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'format': 'mp4',
        'noplaylist': True,
        'progress_hooks': [progress_hook],
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def clean_video(input_path, output_path):
    path_adjusted = os.path.join(os.path.dirname(output_path), ".adjusted_" + os.path.basename(output_path))
    path_rotated = os.path.join(os.path.dirname(output_path), ".rotated_" + os.path.basename(output_path))
    path_watermarked = os.path.join(os.path.dirname(output_path), ".watermarked_" + os.path.basename(output_path))
    try:
        logging.info(f"Adjusting video properties for {input_path}")
        if not adjust_video_properties(input_path, path_adjusted):
            return False

        logging.info(f"Applying random rotation to {path_adjusted}")
        video_clip = VideoFileClip(path_adjusted)
        video_clip = apply_random_rotation(video_clip)
        video_clip.write_videofile(path_rotated, codec='libx264', audio_codec='aac')
        video_clip.close()

        logging.info(f"Adding invisible watermark to {path_rotated}")
        if not add_invisible_watermark_to_video(path_rotated, path_watermarked):
            return False

        logging.info(f"Removing metadata for {path_watermarked}")
        if not remove_metadata(path_watermarked, output_path):
            return False

        logging.info(f"Video cleaned and saved as: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error cleaning video: {e}")
        return False
    finally:
        for temp_file in [path_adjusted, path_rotated, path_watermarked]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
