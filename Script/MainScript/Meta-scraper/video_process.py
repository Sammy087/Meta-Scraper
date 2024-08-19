import os
import cv2
import numpy as np
import pytesseract
import logging
import requests
from youtube_dl import YoutubeDL

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load emoji data (Assuming you have your emoji templates as PNG files)
def load_emoji_templates():
    emoji_templates = []
    emoji_folder = 'templates/emojis'
    for filename in os.listdir(emoji_folder):
        if filename.endswith('.png'):
            template = cv2.imread(os.path.join(emoji_folder, filename), cv2.IMREAD_GRAYSCALE)
            emoji_templates.append(template)
    return emoji_templates

# Load logo templates (Assuming you have your logo templates as PNG files)
def load_logo_templates():
    logo_templates = []
    logo_folder = 'templates/logos'
    for filename in os.listdir(logo_folder):
        if filename.endswith('.png'):
            template = cv2.imread(os.path.join(logo_folder, filename), cv2.IMREAD_GRAYSCALE)
            logo_templates.append(template)
    return logo_templates

# Load other templates (Assuming you have your other templates as PNG files)
def load_other_templates():
    other_templates = []
    other_folder = 'templates/other'
    for filename in os.listdir(other_folder):
        if filename.endswith('.png'):
            template = cv2.imread(os.path.join(other_folder, filename), cv2.IMREAD_GRAYSCALE)
            other_templates.append(template)
    return other_templates

emoji_templates = load_emoji_templates()
logo_templates = load_logo_templates()
other_templates = load_other_templates()

def detect_and_mask_captions(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray_frame)
    
    if text.strip():
        h, w = frame.shape[:2]
        # Masking the area where text is found (this is a rough mask and may need fine-tuning)
        cv2.rectangle(frame, (0, h - 100), (w, h), (0, 0, 0), -1)  # Example mask

    return frame

def detect_and_mask_templates(frame, templates):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    for template in templates:
        h, w = template.shape[:2]
        result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        locations = np.where(result >= threshold)

        for pt in zip(*locations[::-1]):
            # Mask the detected area
            cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (0, 0, 0), -1)

    return frame

def process_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        logging.error(f"Failed to open video file: {input_path}")
        return

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Detect and mask captions
        frame = detect_and_mask_captions(frame)
        
        # Detect and mask logos
        frame = detect_and_mask_templates(frame, logo_templates)
        
        # Detect and mask emojis
        frame = detect_and_mask_templates(frame, emoji_templates)
        
        # Detect and mask other items
        frame = detect_and_mask_templates(frame, other_templates)

        out.write(frame)

    cap.release()
    out.release()
    logging.info(f"Video processed and saved to {output_path}")

def download_video(url, download_path):
    try:
        if url.lower().startswith('http'):
            response = requests.get(url, stream=True)
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logging.info(f"Video downloaded successfully from {url}")
        else:
            ydl_opts = {'outtmpl': download_path}
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logging.info(f"Video downloaded successfully from {url}")
    except Exception as e:
        logging.error(f"Failed to download video from URL: {url}. Error: {e}")
        raise

if __name__ == "__main__":
    # Folder paths
    input_video_folder = '/Users/sammy/Desktop/Meta-Scraper/Script/MainScript/Meta-scraper/videos'
    downloaded_video_path = os.path.join(input_video_folder, 'downloaded_video.mp4')
    
    # Video URL (Replace with actual video URL or pass as argument)
    video_url = 'https://example.com/path_to_input_video.mp4'

    try:
        # Download the video
        download_video(video_url, downloaded_video_path)
        
        # Paths for processing
        input_video_path = downloaded_video_path
        output_video_path = os.path.join(input_video_folder, 'processed_video.mp4')
        
        # Process the video
        process_video(input_video_path, output_video_path)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
