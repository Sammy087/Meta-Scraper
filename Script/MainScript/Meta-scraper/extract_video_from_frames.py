import cv2
import os
import logging

def extract_frames_from_video(video_path, output_folder):
    """
    Extract frames from a video file and save them as images in the specified folder.

    :param video_path: Path to the video file.
    :param output_folder: Folder where frames will be saved.
    :return: List of file paths to the saved frames.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    frames = []
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logging.error(f"Failed to open video file: {video_path}")
        return frames
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_filename = os.path.join(output_folder, f"frame_{frame_count:04d}.png")
        cv2.imwrite(frame_filename, frame)
        frames.append(frame_filename)
        frame_count += 1
    
    cap.release()
    logging.info(f"Extracted {len(frames)} frames from video: {video_path}")
    
    return frames

# Example usage:
video_path = 'path_to_your_video.mp4'
output_folder = 'frames'
extracted_frames = extract_frames_from_video(video_path, output_folder)
print(f"Extracted frames saved to: {extracted_frames}")
