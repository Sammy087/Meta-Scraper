import os
import ffmpeg
from autosub import transcribe

def transcribe_and_add_subtitles(video_path, output_path):
    """
    Transcribe the given video and add subtitles to it.

    Parameters:
    video_path (str): Path to the input video file.
    output_path (str): Path where the output video with subtitles will be saved.
    """
    # Generate transcript
    transcript = transcribe(video_path)

    # Save transcript to a .srt file
    srt_file = video_path.replace('.mp4', '.srt')  # Adjust extension if needed
    with open(srt_file, 'w') as f:
        f.write(transcript)

    # Add subtitles to the video
    ffmpeg.input(video_path).output(output_path, vf=f"subtitles={srt_file}").run()

    # Clean up
    os.remove(srt_file)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python subtitle.py <input_video> <output_video>")
    else:
        video_path = sys.argv[1]
        output_path = sys.argv[2]
        transcribe_and_add_subtitles(video_path, output_path)
