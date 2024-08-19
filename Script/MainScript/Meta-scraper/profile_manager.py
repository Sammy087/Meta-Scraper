import os
import cv2
import numpy as np
import pytesseract
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_emoji_templates():
    emoji_templates = []
    emoji_folder = 'templates/emojis'
    for filename in os.listdir(emoji_folder):
        if filename.endswith('.png'):
            template = cv2.imread(os.path.join(emoji_folder, filename), cv2.IMREAD_GRAYSCALE)
            emoji_templates.append(template)
    return emoji_templates

def load_logo_templates():
    logo_templates = []
    logo_folder = 'templates/logos'
    for filename in os.listdir(logo_folder):
        if filename.endswith('.png'):
            template = cv2.imread(os.path.join(logo_folder, filename), cv2.IMREAD_GRAYSCALE)
            logo_templates.append(template)
    return logo_templates

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
            cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (0, 0, 0), -1)

    return frame

def process_video(input_path, output_path):
    if not os.path.isfile(input_path):
        logging.error(f"Input file does not exist: {input_path}")
        return

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        logging.error(f"Couldn't open video file: {input_path}")
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
        if logo_templates:
            frame = detect_and_mask_templates(frame, logo_templates)
        
        # Detect and mask emojis
        if emoji_templates:
            frame = detect_and_mask_templates(frame, emoji_templates)

        # Detect and mask other elements
        if other_templates:
            frame = detect_and_mask_templates(frame, other_templates)

        out.write(frame)

    cap.release()
    out.release()
    logging.info(f"Video processed and saved to {output_path}")

if __name__ == "__main__":
    input_video_path = 'path_to_input_video.mp4'
    output_video_path = 'path_to_output_video.mp4'
    process_video(input_video_path, output_video_path)
