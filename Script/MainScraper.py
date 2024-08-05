import subprocess
import logging

def remove_metadata(input_file, output_file):
    command = [
        'ffmpeg', '-i', input_file, '-map_metadata', '-1', '-c:v', 'copy', '-c:a', 'copy', output_file
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(f"Error removing metadata: {result.stderr.decode()}")
    return result.returncode == 0

def change_icc_profile(input_file, output_file):
    command = [
        'ffmpeg', '-i', input_file, '-vf', 'format=yuv420p', '-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-c:a', 'copy', output_file
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(f"Error changing ICC profile: {result.stderr.decode()}")
    return result.returncode == 0

def clean_metadata(file_path):
    if not remove_metadata(file_path, file_path):
        logging.error("Failed to remove metadata.")
    if not change_icc_profile(file_path, file_path):
        logging.error("Failed to change ICC profile.")
