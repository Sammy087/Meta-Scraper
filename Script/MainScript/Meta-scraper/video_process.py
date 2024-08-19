import cv2
import logging

def extract_frames_from_video(video_path):
    frames = []
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        logging.error(f"Failed to open video file: {video_path}")
        return frames

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()
    return frames

def recompile_video_from_frames(frames, output_path):
    if not frames:
        logging.error("No frames to compile into video.")
        return None

    try:
        height, width, layers = frames[0].shape
    except IndexError:
        logging.error("Frame list is empty or incorrectly formatted.")
        return None

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))

    for frame in frames:
        out.write(frame)

    out.release()
    return output_path

def process_video_pipeline(video_path):
    frames = extract_frames_from_video(video_path)

    if not frames:
        logging.error(f"No frames extracted from video: {video_path}")
        return None

    output_video_path = recompile_video_from_frames(frames, video_path)
    return output_video_path
