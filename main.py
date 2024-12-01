import os
import openai
import requests
import moviepy.editor as mp
from datetime import datetime
from pytube import YouTube

# Load environment variables
from config.settings import (
    CLAUDE_API_KEY,
    YOUTUBE_API_KEY,
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_USER_ID,
    VIDEO_OUTPUT_DIR
)

# Generate a story using Claude AI
def generate_story():
    story_prompt = (
        "Create a 58-second-long, captivating story that grips the audience, "
        "with engaging dialogue and action. The story must fit into a single minute when read aloud."
    )
    headers = {"Authorization": f"Bearer {CLAUDE_API_KEY}"}
    response = requests.post(
        "https://api.anthropic.com/v1/complete",
        json={"prompt": story_prompt, "max_tokens": 300},
        headers=headers,
    )
    return response.json()["completion"].strip()

# Convert story text to audio
def generate_audio(story_text, output_file):
    from gtts import gTTS
    tts = gTTS(text=story_text, lang="en")
    tts.save(output_file)

# Create video with text, audio, and assets
def create_video(story_text, audio_file, output_video):
    # Prepare background image
    video_clip = mp.ImageClip("assets/background.jpg", duration=58)
    video_clip = video_clip.set_audio(mp.AudioFileClip(audio_file))

    # Add captions
    text_clip = mp.TextClip(
        story_text,
        fontsize=24,
        color="white",
        bg_color="black",
        method="caption",
        size=(720, None),
    ).set_position("bottom").set_duration(58)

    # Composite video
    final_video = mp.CompositeVideoClip([video_clip, text_clip])
    final_video.write_videofile(output_video, fps=24, codec="libx264")

# Upload video to YouTube
def upload_to_youtube(video_path, title, description):
    from googleapiclient.discovery import build
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["story", "shorts"],
            "categoryId": "22",
        },
        "status": {"privacyStatus": "public"},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print(f"Uploaded to YouTube: {response['id']}")

# Upload video to Instagram
def upload_to_instagram(video_url, caption):
    url = f"https://graph.facebook.com/v16.0/{INSTAGRAM_USER_ID}/media"
    params = {
        "media_type": "VIDEO",
        "video_url": video_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        print("Uploaded to Instagram!")
    else:
        print(f"Instagram upload failed: {response.text}")

# Main execution
def main():
    print("Generating story...")
    story = generate_story()
    print("Story generated.")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    audio_file = f"{VIDEO_OUTPUT_DIR}/audio_{timestamp}.mp3"
    video_file = f"{VIDEO_OUTPUT_DIR}/video_{timestamp}.mp4"

    print("Generating audio...")
    generate_audio(story, audio_file)

    print("Creating video...")
    create_video(story, audio_file, video_file)

    print("Uploading to YouTube...")
    title = "Amazing Story: " + story.split(".")[0]  # First sentence as title
    upload_to_youtube(video_file, title, story)

    print("Uploading to Instagram...")
    upload_to_instagram(video_file, story)

    print("Task completed!")

if __name__ == "__main__":
    main()
