import subprocess
import time
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
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip, TextClip
from moviepy.video.fx import rotate
import logging
import os
import re
import cv2
import numpy as np
import json
import pytesseract
import logging
import os
from profile_manager import create_profile, login, delete_profile
import os
import logging
from video_process import process_video_pipeline

# Set up logging
logging.basicConfig(level=logging.INFO)

def main():
    videos_folder = 'videos'
    video_files = [f for f in os.listdir(videos_folder) if os.path.isfile(os.path.join(videos_folder, f))]

    if not video_files:
        logging.info("No videos found in the 'videos' folder. Exiting.")
        return

    for video_file in video_files:
        video_path = os.path.join(videos_folder, video_file)
        logging.info(f"Processing video: {video_path}")

        # Process the video only if it exists
        if os.path.exists(video_path):
            processed_video_path = process_video_pipeline(video_path)
            if processed_video_path:
                logging.info(f"Processed video saved to: {processed_video_path}")
            else:
                logging.error(f"Failed to process video: {video_path}")
        else:
            logging.error(f"Video file not found: {video_path}")

if __name__ == "__main__":
    main()



# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load emoji data
def load_emoji_data(filename='emoji.json'):
    with open(filename, 'r') as f:
        return json.load(f)

emoji_data = load_emoji_data()
emoji_list = [emoji['unicode'] for emoji in emoji_data]

def load_templates():
    """Load grayscale template images."""
    templates = {}
    templates['logo'] = cv2.imread(os.path.join('templates', 'logo_template.png'), cv2.IMREAD_GRAYSCALE)
    templates['emoji'] = cv2.imread(os.path.join('templates', 'emoji_template.png'), cv2.IMREAD_GRAYSCALE)
    return templates

templates = load_templates()

def detect_objects_in_frame(frame):
    """Detect objects in a single video frame using template matching."""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected_objects = []

    for key, template in templates.items():
        if template is not None:
            result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.8
            locations = np.where(result >= threshold)
            for pt in zip(*locations[::-1]):
                detected_objects.append((pt, key))
                # Mask the detected object area
                h, w = template.shape
                cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (0, 0, 0), -1)

    return frame, detected_objects

def detect_emoji_in_frame(frame):
    """Detect emojis in a single video frame."""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected_emojis = []
    for emoji in emoji_list:
        # Create a simple image of the emoji or use an existing template
        emoji_template = np.zeros_like(frame)  # Placeholder for actual emoji image
        result = cv2.matchTemplate(gray_frame, emoji_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        locations = np.where(result >= threshold)
        for pt in zip(*locations[::-1]):
            detected_emojis.append(pt)
            # Mask the detected emoji area
            cv2.rectangle(frame, pt, (pt[0] + emoji_template.shape[1], pt[1] + emoji_template.shape[0]), (0, 0, 0), -1)
    return frame, detected_emojis

def process_video(input_path, output_path):
    """Process video file to detect and mask objects."""
    cap = cv2.VideoCapture(input_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Detect and mask objects (including emojis)
        processed_frame, detected_objects = detect_objects_in_frame(frame)
        processed_frame, detected_emojis = detect_emoji_in_frame(processed_frame)
        out.write(processed_frame)

    cap.release()
    out.release()

def segment_video_to_frames(video_path):
    """Extract frames from a video."""
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def analyze_and_mask_frame(frame):
    """Analyze and mask text, logos, or emojis in a frame."""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect text (captions)
    text = pytesseract.image_to_string(gray_frame)
    if text.strip():
        # Mask text
        frame = cv2.rectangle(frame, (10, 10), (110, 50), (0, 0, 0), -1)  # Example mask

    # Paths to template images
    template_paths = ['templates/logo_template.png', 'templates/emoji_template.png']

    for template_path in template_paths:
        # Load template image and convert to grayscale
        template = cv2.imread(template_path, 0)
        if template is None:
            logging.warning(f"Template {template_path} not found.")
            continue

        # Perform template matching
        res = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(res >= threshold)

        # Draw rectangles around detected areas
        for pt in zip(*loc[::-1]):
            h, w = template.shape[:2]
            cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (0, 0, 0), -1)

    return frame

def recompile_video_from_frames(frames, original_video_path):
    """Recompile video from frames."""
    height, width, layers = frames[0].shape
    fps = 24  # Default FPS value; adjust as needed
    
    # Reconstructing the video
    output_path = original_video_path.replace(".mp4", "_processed.mp4")
    video = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    for frame in frames:
        video.write(frame)

    video.release()
    return output_path

def process_video_pipeline(video_path):
    """Full video processing pipeline."""
    # Step 1: Segment video into frames
    frames = segment_video_to_frames(video_path)

    # Step 2: Analyze and mask frames
    processed_frames = [analyze_and_mask_frame(frame) for frame in frames]

    # Step 3: Recompile the video
    output_video_path = recompile_video_from_frames(processed_frames, video_path)

    return output_video_path

if __name__ == "__main__":
    video_folder = "videos"
    for filename in os.listdir(video_folder):
        if filename.endswith(".mp4"):
            video_path = os.path.join(video_folder, filename)
            print(f"Processing {video_path}...")
            processed_video_path = process_video_pipeline(video_path)
            print(f"Processed video saved at {processed_video_path}")

# User Authentication
def main():
    print("Welcome to the app!")
    action = input("Enter 'register', 'login', or 'delete': ").strip().lower()

    if action == 'register':
        username = input("Enter username: ")
        password = input("Enter password: ")
        email = input("Enter email: ")
        create_profile(username, password, email)
    elif action == 'login':
        username = input("Enter username: ")
        password = input("Enter password: ")
        login(username, password)
    elif action == 'delete':
        username = input("Enter username to delete: ")
        delete_profile(username)
    else:
        print("Invalid action.")
        return

    # Continue to video processing after authentication
    if __name__ == "__main__":
        import sys
        if len(sys.argv) != 3:
            print("Usage: python main.py <input_video> <output_video>")
        else:
            video_path = sys.argv[1]
            output_path = sys.argv[2]
            process_video(video_path, output_path)

# Process video
def process_video(video_path, output_path):
 (video_path, output_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_video> <output_video>")
    else:
        video_path = sys.argv[1]
        output_path = sys.argv[2]
        process_video(video_path, output_path)


def generate_background_image(width, height):
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    background = ColorClip((width, height), color=color)
    return background


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

def crop_video(input_path, output_path, crop_amount=10):
    video = VideoFileClip(input_path)
    cropped_video = video.crop(x1=crop_amount, y1=crop_amount, x2=video.w-crop_amount, y2=video.h-crop_amount)
    cropped_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
    video.close()
    cropped_video.close()
    logging.info(f"Cropped video saved as: {output_path}")

def sanitize_filename(filename):
    # Replace non-alphanumeric characters with underscores and limit length
    filename = re.sub(r'[^\w\s]', '_', filename)
    return filename[:150]  # Adjust length as needed

from moviepy.editor import AudioFileClip, CompositeAudioClip

def manage_background_noise(input_video_path, output_video_path):
    video = VideoFileClip(input_video_path)
    
    # If there's background noise, remove it
    if "detect" in dir(video.audio):
        filtered_audio = video.audio.volumex(0.5)  # Example: Lowering volume by 50%
    else:
        # Add background noise
        noise_clip = AudioFileClip("background_noise.mp3").volumex(0.1)
        filtered_audio = CompositeAudioClip([video.audio, noise_clip])
    
    video = video.set_audio(filtered_audio)
    video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
    video.close()
    logging.info(f"Background noise managed and video saved as: {output_video_path}")

def manipulate_frames(input_path, output_path):
    video = VideoFileClip(input_path)
    frame_list = list(video.iter_frames())
    
    # Randomly delete frames
    frame_list = [frame for i, frame in enumerate(frame_list) if i % random.randint(1, 10) != 0]

    # Recreate video
    new_video = VideoFileClip(input_path).set_duration(len(frame_list)/video.fps).set_fps(video.fps)
    new_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
    video.close()
    new_video.close()
    logging.info(f"Frame-manipulated video saved as: {output_path}")

def download_video(url, output_path):
    # Ensure output_path exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    def progress_hook(d):
        if d['status'] == 'finished':
            print(f"Done downloading video: {d['filename']}")

    # Use youtube_dl to download video
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'format': 'mp4',
        'noplaylist': True,
        'progress_hooks': [progress_hook],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)  # Get video info without downloading
        if 'title' in info_dict:
            title = sanitize_filename(info_dict['title'])
            output_path_sanitized = os.path.join(output_path, f"{title}.%(ext)s")
            ydl_opts['outtmpl']['default'] = output_path_sanitized
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
        txt_clip = txt_clip.set_position(('right', 'bottom')).set_duration(video.duration)

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
        'ffmpeg', '-i', input_file, '-vf', 'format=yuv420p', '-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-c:a',
        'copy', output_file
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
            logging.warning(f"Attempt {attempt + 1}/{max_retries} failed to remove file {filepath}: {e}")
            time.sleep(1)
    return False


def clean_video(input_path, output_path):
    path_adjusted = os.path.join(os.path.dirname(output_path), ".adjusted_" + os.path.basename(output_path))
    path_rotated = os.path.join(os.path.dirname(output_path), ".rotated_" + os.path.basename(output_path))
    path_watermarked = os.path.join(os.path.dirname(output_path), ".watermarked_" + os.path.basename(output_path))
    try:
        # Adjust video properties
        logging.info(f"Adjusting video properties for {input_path}")
        if not adjust_video_properties(input_path, path_adjusted):
            return False

        if not os.path.exists(path_adjusted):
            logging.error(f"Error: temp file {path_adjusted} does not exist after adjusting video properties.")
            return False

        # Apply random rotation
        logging.info(f"Applying random rotation to {path_adjusted}")
        video_clip = VideoFileClip(path_adjusted)
        video_clip = apply_random_rotation(video_clip)
        video_clip.write_videofile(path_rotated, codec='libx264', audio_codec='aac')
        video_clip.close()

        # Add invisible watermark
        logging.info(f"Adding invisible watermark to {path_rotated}")
        if not add_invisible_watermark_to_video(path_rotated, path_watermarked):
            return False

        # Remove all metadata
        logging.info(f"Removing metadata for {path_watermarked}")
        if not remove_metadata(path_watermarked, output_path):
            return False

        logging.info(f"Video cleaned and saved as: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error cleaning video: {e}")
        return False
    finally:
        # Clean up all temporary files
        for temp_file in [path_adjusted, path_rotated, path_watermarked]:
            if os.path.exists(temp_file):
                os.remove(temp_file)


def cleanup_temp_files():
    for temp_file in os.listdir('.'):
        if temp_file.startswith('temp'):
            force_close_file(temp_file)

import dash
from dash import dcc, html, Output, Input, State, ctx
import dash_bootstrap_components as dbc
import base64
import os
import random
import logging
import time
from flask import send_from_directory, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Define the directory where processed videos are saved
processed_video_dir = "videos"
assets_dir = "assets"
db_file = "users.db"

# Initialize the SQLite database
def init_db():
    with sqlite3.connect(db_file) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                asset_path TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

init_db()

# Serve the processed videos
@app.server.route('/videos/<path:filename>')
def download_file(filename):
    return send_from_directory(processed_video_dir, filename, as_attachment=True)

# App Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    html.Button(html.Img(src='assets/profile_icon.png', style={'width': '24px', 'height': '24px'}),
                                id='profile-btn', n_clicks=0, style={'float': 'right', 'border': 'none'}),
                ], width='auto')
            ]),
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
                    dbc.Label("Number of Variations:"),
                    dcc.Slider(
                        id='variation-slider',
                        min=1,
                        max=30,
                        step=1,
                        value=1,
                        marks={i: str(i) for i in range(1, 31)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button('Process', id='process-btn', n_clicks=0, color='primary', className="btn-block")
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        id="loading-spinner",
                        type="circle",
                        children=html.Div(id="processing-output"),
                        fullscreen=True
                    )
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button('Download Videos', id='download-btn', color='success', className="btn-block mt-3"),
                    dcc.Download(id="download-component")
                ])
            ])
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
            html.P(
                "This process helps to obfuscate the video's origin and make it more difficult to detect as a reupload.",
                className="mt-3 text-muted"),
        ], md=8, className="offset-md-2")
    ], className="mt-4 mb-5"),
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Profile")),
        dbc.ModalBody([
            dbc.Tabs([
                dbc.Tab([
                    html.Div([
                        dbc.Input(id='login-email', type='email', placeholder='Email'),
                        dbc.Input(id='login-password', type='password', placeholder='Password'),
                        dbc.Button('Login', id='login-btn', n_clicks=0, color='primary', className='mt-2')
                    ])
                ], label="Login"),
                dbc.Tab([
                    html.Div([
                        dbc.Input(id='signup-email', type='email', placeholder='Email'),
                        dbc.Input(id='signup-password', type='password', placeholder='Password'),
                        dbc.Button('Sign Up', id='signup-btn', n_clicks=0, color='primary', className='mt-2')
                    ])
                ], label="Sign Up"),
                dbc.Tab([
                    html.Div([
                        dbc.Button('Logout', id='logout-btn', n_clicks=0, color='secondary', className='mt-2')
                    ])
                ], label="Logout")
            ])
        ]),
        dbc.ModalFooter(dbc.Button('Close', id='close-modal', className='ml-auto'))
    ], id='profile-modal', is_open=False),
    dcc.Store(id='user-data', data={}),  # Store user session data
    dcc.Store(id='download-urls', data=[]),  # To store the download URLs
], fluid=True)

# Profile modal callback
@app.callback(
    Output('profile-modal', 'is_open'),
    [Input('profile-btn', 'n_clicks'),
     Input('close-modal', 'n_clicks')],
    [State('profile-modal', 'is_open')]
)
def toggle_modal(profile_btn, close_modal, is_open):
    if ctx.triggered_id == 'profile-btn':
        return not is_open
    if ctx.triggered_id == 'close-modal':
        return not is_open
    return is_open

# Unified authentication callback
@app.callback(
    Output('user-data', 'data'),
    [Input('login-btn', 'n_clicks'),
     Input('signup-btn', 'n_clicks'),
     Input('logout-btn', 'n_clicks')],
    [State('login-email', 'value'),
     State('login-password', 'value'),
     State('signup-email', 'value'),
     State('signup-password', 'value')]
)
def handle_authentication(login_clicks, signup_clicks, logout_clicks, login_email, login_password, signup_email, signup_password):
    triggered_id = ctx.triggered_id

    if triggered_id == 'login-btn' and login_email and login_password:
        with sqlite3.connect(db_file) as conn:
            c = conn.cursor()
            c.execute('SELECT password FROM users WHERE email = ?', (login_email,))
            user = c.fetchone()
            if user and check_password_hash(user[0], login_password):
                session['email'] = login_email
                return {'email': login_email}
    
    elif triggered_id == 'signup-btn' and signup_email and signup_password:
        hashed_password = generate_password_hash(signup_password)
        with sqlite3.connect(db_file) as conn:
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (signup_email, hashed_password))
                conn.commit()
                session['email'] = signup_email
                return {'email': signup_email}
            except sqlite3.IntegrityError:
                logging.error('User already exists.')

    elif triggered_id == 'logout-btn':
        session.pop('email', None)
        return {}

    return dash.no_update

# Update output callback
@app.callback(
    [Output('upload-status', 'children'),
     Output('file-name', 'children'),
     Output('processing-output', 'children'),
     Output('download-urls', 'data')],
    [Input('process-btn', 'n_clicks')],
    [State('video-url', 'value'),
     State('upload-data', 'contents'),
     State('variation-slider', 'value'),
     State('user-data', 'data')]
)
def update_output(n_clicks, video_url, file_contents, num_variations, user_data):
    if n_clicks > 0:
        urls = []
        upload_status = "No URL or file uploaded."
        file_name = ""
        processed_files = []

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
            processed_files = process_urls(urls, num_variations)
            if processed_files:
                # Save user assets if logged in
                if 'email' in user_data:
                    user_email = user_data['email']
                    user_id = get_user_id(user_email)
                    if user_id:
                        save_user_assets(user_id, processed_files)
                return [upload_status, file_name, "Processing complete. You can now download the videos.", processed_files]

        return [upload_status, file_name, "Processing failed or no URLs provided.", []]

    return ["", "", "", []]

# Download callback
@app.callback(
    Output('download-component', 'data'),
    Input('download-btn', 'n_clicks'),
    State('download-urls', 'data')
)
def trigger_download(n_clicks, download_urls):
    if n_clicks and n_clicks > 0 and download_urls:
        # Handle the first file in the list
        first_file = download_urls[0]
        if os.path.exists(first_file):
            logging.info(f"Triggering download for: {first_file}")
            return dcc.send_file(first_file)
        else:
            logging.error(f"File does not exist: {first_file}")

    return dash.no_update

# Update output callback
@app.callback(
    [Output('upload-status', 'children'),
     Output('file-name', 'children'),
     Output('processing-output', 'children'),
     Output('download-urls', 'data')],
    [Input('process-btn', 'n_clicks')],
    [State('video-url', 'value'),
     State('upload-data', 'contents'),
     State('variation-slider', 'value'),
     State('user-data', 'data')]
)
def update_output(n_clicks, video_url, file_contents, num_variations, user_data):
    if n_clicks > 0:
        urls = []
        upload_status = "No URL or file uploaded."
        file_name = ""
        processed_files = []

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
            processed_files = process_urls(urls, num_variations)
            if processed_files:
                # Save user assets if logged in
                if 'email' in user_data:
                    user_email = user_data['email']
                    user_id = get_user_id(user_email)
                    if user_id:
                        save_user_assets(user_id, processed_files)
                return [upload_status, file_name, "Processing complete. You can now download the videos.", processed_files]

        return [upload_status, file_name, "Processing failed or no URLs provided.", []]

    return ["", "", "", []]

# Download callback
@app.callback(
    Output('download-component', 'data'),
    Input('download-btn', 'n_clicks'),
    State('download-urls', 'data')
)
def trigger_download(n_clicks, download_urls):
    if n_clicks and n_clicks > 0 and download_urls:
        # Handle the first file in the list
        first_file = download_urls[0]
        if os.path.exists(first_file):
            logging.info(f"Triggering download for: {first_file}")
            return dcc.send_file(first_file)
        else:
            logging.error(f"File does not exist: {first_file}")

    return dash.no_update

def process_urls(urls, num_variations):
    output_path = processed_video_dir
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    processed_files = []

    for video_url in urls:
        logging.info(f"Processing URL: {video_url}")
        try:
            # Simulate processing delay for demonstration
            time.sleep(5)

            # Step 1: Download video
            download_video(video_url, output_path)

            # Step 2: Find the downloaded video file
            downloaded_files = [f for f in os.listdir(output_path) if
                                os.path.isfile(os.path.join(output_path, f)) and not f.startswith('cleaned_')]
            if downloaded_files:
                for downloaded_file in downloaded_files:
                    input_video_path = os.path.join(output_path, downloaded_file)

                    # Generate the specified number of variations
                    for i in range(num_variations):
                        unique_suffix = random.randint(1000, 9999)
                        output_video_path = os.path.join(output_path, f'cleaned_{unique_suffix}_{downloaded_file}')

                        # Ensure cleanup of temporary files before processing the next video
                        cleanup_temp_files()

                        # Step 3: Clean the video (adjust video properties, remove metadata, change ICC profile, split and concatenate)
                        if clean_video(input_video_path, output_video_path):
                            logging.info(
                                f'Video variation {i + 1}/{num_variations} downloaded and edited successfully! Edited video saved as: {output_video_path}')
                            processed_files.append(output_video_path)
                        else:
                            logging.error(f'Failed to clean video variation {i + 1}/{num_variations}: {input_video_path}')

                    os.remove(input_video_path)  # Remove the original downloaded file after generating all variations
            else:
                logging.error('Error: No video found in the output directory.')
        except Exception as e:
            logging.error(f"Error processing URL {video_url}: {e}")

    return processed_files

def cleanup_temp_files():
    temp_files = [f for f in os.listdir(processed_video_dir) if f.endswith('.temp')]
    for temp_file in temp_files:
        os.remove(os.path.join(processed_video_dir, temp_file))

def get_user_id(email):
    with sqlite3.connect(db_file) as conn:
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        return user[0] if user else None

def save_user_assets(user_id, assets):
    with sqlite3.connect(db_file) as conn:
        c = conn.cursor()
        for asset in assets:
            c.execute('INSERT INTO user_assets (user_id, asset_path) VALUES (?, ?)', (user_id, asset))
        conn.commit()

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')

def process_media(input_path, output_path, num_copies, watermark_text="Sample Watermark"):
    try:
        for i in range(num_copies):
            # Process video or image
            if input_path.lower().endswith(('mp4', 'mov', 'avi')):
                output_video_path = f"{output_path}_copy_{i + 1}.mp4"
                add_watermark_to_video(input_path, output_video_path, watermark_text)
            elif input_path.lower().endswith(('jpg', 'jpeg', 'png')):
                output_image_path = f"{output_path}_copy_{i + 1}.jpg"
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