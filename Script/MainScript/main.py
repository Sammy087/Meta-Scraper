import logging
import os
import random
import subprocess
import time
import json
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip, TextClip
from PIL import Image, ImageDraw, ImageFont
import yt_dlp as youtube_dl
import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import base64
import numpy as np
import os
import random
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
import logging
from tqdm import tqdm
import os
import re


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_background_image(width, height):
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    background = ColorClip((width, height), color=color)
    return background

from moviepy.video.fx import rotate

def apply_random_rotation(video_clip):
    # Generate a random rotation angle between -3 and 3 degrees
    angle = random.uniform(-3, 3)
    rotated_clip = rotate(video_clip, angle)
    return rotated_clip

def wait_for_file_release(filepath, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open(filepath, 'a'):
                pass
            return True
        except PermissionError:
            time.sleep(0.5)
    return False


def sanitize_filename(filename):
    # Replace non-alphanumeric characters with underscores and limit length
    filename = re.sub(r'[^\w\s]', '_', filename)
    return filename[:150]  # Adjust length as needed

def progress_hook(d):
    if d['status'] == 'finished':
        print(f"Done downloading video: {d['filename']}")

def download_video(url, output_path):
    # Ensure output_path exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Use youtube_dl to download video
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'format': 'best',
        'noplaylist': True,
        'progress_hooks': [progress_hook],  # Ensure the progress hook is defined
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)  # Get video info without downloading
        if 'title' in info_dict:
            title = sanitize_filename(info_dict['title'])
            output_path_sanitized = os.path.join(output_path, f"{title}.%(ext)s")
            ydl_opts['outtmpl'] = output_path_sanitized
        ydl.download([url])


def add_watermark_to_image(input_image_path, output_image_path, watermark_text="Sample Watermark"):
    try:
        image = Image.open(input_image_path).convert("RGBA")
        watermark = Image.new("RGBA", image.size)
        draw = ImageDraw.Draw(watermark, "RGBA")
        
        font_size = 36
        font = ImageFont.truetype("arial.ttf", font_size)
        text_width, text_height = draw.textsize(watermark_text, font=font)
        text_position = (image.width - text_width - 10, image.height - text_height - 10)
        
        draw.text(text_position, watermark_text, font=font, fill=(255, 255, 255, 128))  # Semi-transparent watermark
        
        watermarked_image = Image.alpha_composite(image, watermark)
        watermarked_image.save(output_image_path)
        logging.info(f"Watermark added and image saved as: {output_image_path}")
        return True
    except Exception as e:
        logging.error(f"Error adding watermark to image: {e}")
        return False

def add_watermark_to_video(input_video_path, output_video_path, watermark_text="Sample Watermark"):
    try:
        video = VideoFileClip(input_video_path)
        
        # Create a TextClip for the watermark
        txt_clip = TextClip(watermark_text, fontsize=36, color='white', bg_color='transparent')
        
        # Set the position and duration of the watermark
        txt_clip = txt_clip.set_pos(('right', 'bottom')).set_duration(video.duration)
        
        # Combine the original video with the watermark
        watermarked_video = CompositeVideoClip([video, txt_clip])
        
        # Write the result to a file
        watermarked_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
        
        # Close the video clips
        video.close()
        watermarked_video.close()
        
        logging.info(f"Watermark added and video saved as: {output_video_path}")
        return True
    except Exception as e:
        logging.error(f"Error adding watermark to video: {e}")
        return False


def add_invisible_watermark_to_video(input_video_path, output_video_path, watermark_text="Sample Watermark"):
    try:
        video = VideoFileClip(input_video_path)
        txt_clip = TextClip(watermark_text, fontsize=24, color='white', bg_color='transparent')
        
        # Set the watermark to be semi-transparent
        txt_clip = txt_clip.set_opacity(0.1)  # Adjust opacity as needed
        txt_clip = txt_clip.set_pos(('right', 'bottom')).set_duration(video.duration)
        
        watermarked_video = CompositeVideoClip([video, txt_clip])
        watermarked_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
        video.close()
        watermarked_video.close()
        logging.info(f"Watermark added and video saved as: {output_video_path}")
        return True
    except Exception as e:
        logging.error(f"Error adding watermark to video: {e}")
        return False

def apply_random_rotation(video_clip):
    import numpy as np
    import random

    angle = random.uniform(-3, 3)  # Random rotation between -3 and 3 degrees
    return video_clip.rotate(angle)

def adjust_video_properties(input_path, output_path):
    try:
        saturation = random.uniform(0.9, 1.1)
        contrast = random.uniform(0.95, 1.05)
        highlight = random.uniform(0.95, 1.05)
        sharpness = random.uniform(-0.5, 0.5)
        
        ffmpeg_command = [
            'ffmpeg', '-i', input_path, '-vf',
            f"eq=saturation={saturation}:contrast={contrast}:gamma={highlight},unsharp=5:5:{sharpness}",
            '-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-c:a', 'copy', output_path
        ]
        
        result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logging.error(f"Error adjusting video properties: {result.stderr.decode()}")
            return False
        
        logging.info(f"Video properties adjusted and video written to {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error adjusting video properties: {e}")
        return False
    
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
            logging.warning(f"Attempt {attempt+1}/{max_retries} failed to remove file {filepath}: {e}")
            time.sleep(1)
    return False

def clean_video(input_path, output_path):
    temp_output1 = f"temp1_video_{random.randint(1000, 9999)}.mp4"
    temp_output2 = f"temp2_video_{random.randint(1000, 9999)}.mp4"
    try:
        # Adjust video properties
        logging.info(f"Adjusting video properties for {input_path}")
        if not adjust_video_properties(input_path, temp_output1):
            return False
        
        if not os.path.exists(temp_output1):
            logging.error(f"Error: temp file {temp_output1} does not exist after adjusting video properties.")
            return False
        
        # Apply random rotation
        logging.info(f"Applying random rotation to {temp_output1}")
        video_clip = VideoFileClip(temp_output1)
        video_clip = apply_random_rotation(video_clip)
        temp_output2 = f"rotated_{temp_output1}"
        video_clip.write_videofile(temp_output2, codec='libx264', audio_codec='aac')
        video_clip.close()
        
        # Add invisible watermark
        logging.info(f"Adding invisible watermark to {temp_output2}")
        final_output_path = f"watermarked_{random.randint(1000, 9999)}_{output_path}"
        if not add_invisible_watermark_to_video(temp_output2, final_output_path):
            return False
        
        # Remove all metadata
        logging.info(f"Removing metadata for {final_output_path}")
        if not remove_metadata(final_output_path, output_path):
            return False
        
        logging.info(f"Video cleaned and saved as: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error cleaning video: {e}")
        return False
    finally:
        # Clean up all temporary files
        for temp_file in [temp_output1, temp_output2]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

def cleanup_temp_files():
    for temp_file in os.listdir('.'):
        if temp_file.startswith('temp'):
            force_close_file(temp_file)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("TikTok Video Downloader & Cleaner", className="text-center mb-4"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("TikTok Video URL:"),
                    dbc.Input(id='video-url', type='text', placeholder='Enter TikTok video URL or upload a file with URLs')
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Upload File with URLs:"),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=False
                    ),
                    html.Div(id='file-name', className='mt-2'),
                    html.Div(id='upload-status', className='mt-2')
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button('Download and Clean', id='submit-val', n_clicks=0, color='primary', className="btn-block")
                ])
            ]),
        ], md=6, className="offset-md-3")
    ], className="mt-5"),
    dbc.Row([
        dbc.Col([
            html.H4("What the Bot Does:", className="text-center mt-5 mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.H5("Video Download and Processing", className="card-title"),
                    html.Ul([
                        html.Li("Downloads the TikTok video using yt-dlp."),
                        html.Li("Removes all metadata to enhance privacy."),
                        html.Li("Adjusts video properties:", className="mt-2"),
                        html.Ul([
                            html.Li("Randomly adjusts saturation (±10%)."),
                            html.Li("Randomly adjusts contrast (±5%)."),
                            html.Li("Randomly adjusts gamma/highlight (±5%)."),
                            html.Li("Applies random sharpness adjustment."),
                        ]),
                        html.Li("Changes ICC profile and color space."),
                        html.Li("Adds a watermark:", className="mt-2"),
                        html.Ul([
                            html.Li("Adds a semi-transparent watermark to the video."),
                        ]),
                        html.Li("Saves the processed video and deletes the original."),
                    ])
                ])
            ]),
            html.P("This process helps to obfuscate the video's origin and make it more difficult to detect as a reupload.", className="mt-3 text-muted"),
        ], md=8, className="offset-md-2")
    ], className="mt-4 mb-5")
], fluid=True)

def process_urls(urls):
    output_path = "videos"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for video_url in urls:
        logging.info(f"Processing URL: {video_url}")
        try:
            # Step 1: Download video
            download_video(video_url, output_path)
            
            # Step 2: Find the downloaded video file
            downloaded_files = [f for f in os.listdir(output_path) if os.path.isfile(os.path.join(output_path, f)) and not f.startswith('cleaned_')]
            if downloaded_files:
                for downloaded_file in downloaded_files:
                    input_video_path = os.path.join(output_path, downloaded_file)
                    unique_suffix = random.randint(1000, 9999)
                    output_video_path = os.path.join(output_path, f'cleaned_{unique_suffix}_{downloaded_file}')
                    
                    # Ensure cleanup of temporary files before processing the next video
                    cleanup_temp_files()
                    
                    # Step 3: Clean the video (adjust video properties, remove metadata, change ICC profile, split and concatenate)
                    if clean_video(input_video_path, output_video_path):
                        logging.info(f'Video downloaded and edited successfully! Edited video saved as: {output_video_path}')
                        os.remove(input_video_path)  # Remove the original downloaded file
                    else:
                        logging.error(f'Failed to clean video: {input_video_path}')
            else:
                logging.error('Error: No video found in the output directory.')
        except Exception as e:
            logging.error(f"Error processing URL {video_url}: {e}")

@app.callback(
    [Output('upload-status', 'children'), Output('file-name', 'children')],
    [Input('submit-val', 'n_clicks')],
    [State('video-url', 'value'),
     State('upload-data', 'contents')]
)
def update_output(n_clicks, video_url, file_contents):
    if n_clicks > 0:
        urls = []
        upload_status = "No URL or file uploaded."
        file_name = ""

        if file_contents:
            content_type, content_string = file_contents.split(',')
            decoded = base64.b64decode(content_string)
            urls = decoded.decode('utf-8').splitlines()
            upload_status = "File uploaded successfully!"
            file_name = "Uploaded file with URLs."

        elif video_url:
            urls = [video_url]
            upload_status = "URL processed successfully!"
            file_name = ""

        if urls:
            process_urls(urls)
        return [upload_status, file_name]

    return ["", ""]

if __name__ == '__main__':
    app.run_server(debug=True)

def process_media(input_path, output_path, num_copies, watermark_text="Sample Watermark"):
    try:
        for i in range(num_copies):
            # Process video or image
            if input_path.lower().endswith(('mp4', 'mov', 'avi')):
                output_video_path = f"{output_path}_copy_{i+1}.mp4"
                add_watermark_to_video(input_path, output_video_path, watermark_text)
            elif input_path.lower().endswith(('jpg', 'jpeg', 'png')):
                output_image_path = f"{output_path}_copy_{i+1}.jpg"
                # Add image processing here
                pass
            # Clean metadata here
            clean_metadata(output_video_path if 'output_video_path' in locals() else output_image_path)

        logging.info("Processing completed for multiple media files.")
        return True
    except Exception as e:
        logging.error(f"Error processing media: {e}")
        return False

def add_watermark_to_video(input_video_path, output_video_path, watermark_text="Sample Watermark"):
    try:
        video = VideoFileClip(input_video_path)
        txt_clip = TextClip(watermark_text, fontsize=36, color='white', bg_color='transparent')
        txt_clip = txt_clip.set_pos(('right', 'bottom')).set_duration(video.duration)
        
        watermarked_video = CompositeVideoClip([video, txt_clip])
        watermarked_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
        video.close()
        watermarked_video.close()
        logging.info(f"Watermark added and video saved as: {output_video_path}")
        return True
    except Exception as e:
        logging.error(f"Error adding watermark to video: {e}")
        return False

def clean_metadata(file_path):
    # Implement metadata cleaning logic here
    pass

def main():
    input_path = input("Enter the path of the video or image: ")
    output_path = input("Enter the output path: ")
    num_copies = int(input("Enter the number of copies to create: "))
    watermark_text = input("Enter watermark text (optional): ")

    process_media(input_path, output_path, num_copies, watermark_text)

if __name__ == "__main__":
    main()
