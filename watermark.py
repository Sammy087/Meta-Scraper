from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from PIL import Image, ImageDraw, ImageFont
import logging

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

def add_invisible_watermark_to_video(input_video_path, output_video_path, watermark_text="Sample Watermark"):
    try:
        video = VideoFileClip(input_video_path)
        txt_clip = TextClip(watermark_text, fontsize=24, color='white', bg_color='transparent')
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
