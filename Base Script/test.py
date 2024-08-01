import logging
import os
import random
import subprocess
import time
import json
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip
import yt_dlp as youtube_dl
import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import base64

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_background_image(width, height):
    # Generate a random color
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    # Create a ColorClip with the random color
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

def download_video(url, output_path):
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'format': 'best',
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

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

def get_video_info(input_path):
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', input_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    data = json.loads(result.stdout)
    duration = float(data['format']['duration'])
    video_stream = next(s for s in data['streams'] if s['codec_type'] == 'video')
    framerate = eval(video_stream['r_frame_rate'])
    return duration, framerate

def split_video_ffmpeg(input_path):
    segment_paths = []
    first_segment_path = f"segment_1_{random.randint(1000, 9999)}.mp4"
    second_segment_path = f"segment_2_{random.randint(1000, 9999)}.mp4"
    
    duration, framerate = get_video_info(input_path)
    mid_point = duration / 2
    
    # Calculate the exact frame number for the mid-point
    mid_frame = int(mid_point * framerate)
    mid_point_exact = mid_frame / framerate

    # Split the video into two parts
    subprocess.run([
        'ffmpeg', '-i', input_path, 
        '-t', str(mid_point_exact), 
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', 
        '-c:a', 'aac', '-b:a', '192k',
        '-avoid_negative_ts', 'make_zero',
        first_segment_path
    ])
    subprocess.run([
        'ffmpeg', '-i', input_path, 
        '-ss', str(mid_point_exact), 
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', 
        '-c:a', 'aac', '-b:a', '192k',
        second_segment_path
    ])
    
    segment_paths.append(first_segment_path)
    segment_paths.append(second_segment_path)
    
    return segment_paths

def concatenate_videos_ffmpeg(segment_paths, output_path):
    with open("concat_list.txt", "w") as f:
        for segment_path in segment_paths:
            f.write(f"file '{segment_path}'\n")
    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'concat_list.txt', 
        '-c', 'copy', '-movflags', '+faststart', 
        output_path
    ])
    # Clean up
    os.remove("concat_list.txt")
    for segment_path in segment_paths:
        os.remove(segment_path)

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
    temp_output3 = f"temp3_video_{random.randint(1000, 9999)}.mp4"
    temp_output4 = f"temp4_video_{random.randint(1000, 9999)}.mp4"
    try:
        # Adjust video properties
        logging.info(f"Adjusting video properties for {input_path}")
        if not adjust_video_properties(input_path, temp_output1):
            return False
        
        if not os.path.exists(temp_output1):
            logging.error(f"Error: temp file {temp_output1} does not exist after adjusting video properties.")
            return False
        
        # Remove all metadata
        logging.info(f"Removing metadata for {temp_output1}")
        if not remove_metadata(temp_output1, temp_output2):
            return False
        
        if not force_close_file(temp_output1):
            return False
        
        if not os.path.exists(temp_output2):
            logging.error(f"Error: temp file {temp_output2} does not exist after metadata removal.")
            return False
        
        # Change ICC profile (approximated)
        logging.info(f"Changing ICC profile for {temp_output2}")
        if not change_icc_profile(temp_output2, temp_output3):
            return False
        
        if not force_close_file(temp_output2):
            return False
        
        # Split the video into 2 parts
        logging.info(f"Adding background image to {temp_output3}")
        video = VideoFileClip(temp_output3)
        bg_width = random.randint(int(video.w * 0.8), video.w)
        bg_height = random.randint(int(video.h * 0.8), video.h)
        background = generate_background_image(bg_width, bg_height)
        background = background.set_opacity(0).set_duration(video.duration)
        
        # Center the background
        pos_x = (video.w - bg_width) // 2
        pos_y = (video.h - bg_height) // 2
        
        final = CompositeVideoClip([video, background.set_position((pos_x, pos_y))])
        final.write_videofile(temp_output4, codec='libx264', audio_codec='aac')
        video.close()
        final.close()
        
        if not force_close_file(temp_output3):
            return False
        
        # Split the video into 2 parts
        logging.info(f"Splitting video {temp_output4}")
        segment_paths = split_video_ffmpeg(temp_output4)
        if not segment_paths:
            return False
        
        # Concatenate the segments back together
        logging.info(f"Concatenating video segments")
        concatenate_videos_ffmpeg(segment_paths, output_path)
        
        logging.info(f"Video cleaned and saved as: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error cleaning video: {e}")
        return False
    finally:
        # Clean up all temporary files
        for temp_file in [temp_output1, temp_output2, temp_output3, temp_output4]:
            if os.path.exists(temp_file):
                force_close_file(temp_file)

def cleanup_temp_files():
    for temp_file in os.listdir('.'):
        if temp_file.startswith('temp') or temp_file.startswith('segment_'):
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
                        html.Li("Adds an invisible background image:", className="mt-2"),
                        html.Ul([
                            html.Li("Generates a random color background."),
                            html.Li("Sets dimensions to 80-100% of video size."),
                            html.Li("Applies zero opacity (invisible)."),
                            html.Li("Centers the background in the video."),
                        ]),
                        html.Li("Video Splitting and Concatenation:", className="mt-2"),
                        html.Ul([
                            html.Li("Splits the video into parts using FFmpeg."),
                            html.Li("Concatenates the parts back together."),
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