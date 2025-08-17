import os
import requests
from googletrans import Translator
from gtts import gTTS
import facebook
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

# --- Configuration ---
# It is recommended to set these as environment variables for security.
# The script will use the environment variable if it exists, otherwise it will use the hardcoded value.
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "YOUR_FACEBOOK_PAGE_ID")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "YOUR_FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "YOUR_FACEBOOK_APP_SECRET")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "YOUR_FACEBOOK_ACCESS_TOKEN")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "YOUR_YOUTUBE_CHANNEL_ID")

# --- Helper Functions ---

def get_latest_youtube_video(api_key, channel_id):
    """Gets the latest video from a YouTube channel."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=1,
        order="date",
        type="video"
    )
    response = request.execute()
    if response['items']:
        return response['items'][0]['id']['videoId']
    return None

def get_video_transcript(video_id):
    """Fetches the transcript for a YouTube video."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript_list])
    except Exception as e:
        print(f"Error getting transcript: {e}")
        return None

def translate_text(text, dest_language='en'):
    """Translates text to the destination language."""
    translator = Translator()
    translation = translator.translate(text, dest=dest_language)
    return translation.text

def generate_audio_from_text(text, filename="kirtan_audio.mp3"):
    """Generates an MP3 audio file from text."""
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(filename)
    return filename

def post_to_facebook_page(page_id, access_token, message, video_path=None):
    """Posts a message and optionally a video to a Facebook page."""
    graph = facebook.GraphAPI(access_token)
    if video_path:
        with open(video_path, 'rb') as video_file:
            graph.put_video(
                video_file,
                description=message,
                published=True, # Set to False to upload as a draft
                # other parameters as needed
            )
        print("Video posted to Facebook.")
    else:
        graph.put_object(
            parent_object=page_id,
            connection_name='feed',
            message=message
        )
        print("Text message posted to Facebook.")


# --- Main Pipeline ---

def main():
    """Main function to run the Kirtan pipeline."""
    print("Starting the Kirtan pipeline...")

    # 1. Get the latest YouTube video
    print("Fetching the latest YouTube video...")
    video_id = get_latest_youtube_video(YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID)
    if not video_id:
        print("No new videos found. Exiting.")
        return

    print(f"Found video with ID: {video_id}")

    # 2. Get the video transcript
    print("Fetching video transcript...")
    transcript = get_video_transcript(video_id)
    if not transcript:
        print("Could not retrieve transcript. Exiting.")
        return

    # 3. Translate the transcript (if necessary)
    # Assuming the Kirtan is in a language that needs translation to English for a wider audience.
    print("Translating transcript...")
    translated_text = translate_text(transcript)
    print("Translated Text:", translated_text[:200] + "...") # Print a snippet

    # 4. Human Review Point (Conceptual)
    # In a real-world scenario, you would save the translated_text
    # to a file or database and have a human review it before proceeding.
    print("\n--- HUMAN REVIEW REQUIRED ---")
    print("Please review the translated text before it is published.")
    print("To continue automatically, remove the input() call below.")
    # input("Press Enter to continue after reviewing the text...")

    # 5. Generate Audio (Optional, if creating an audio post)
    # print("Generating audio from translated text...")
    # audio_file = generate_audio_from_text(translated_text)
    # print(f"Audio file created: {audio_file}")

    # 6. Post to Facebook
    print("Posting to Facebook...")
    post_message = f"Listen to the latest Kirtan!\n\nEnglish Translation:\n{translated_text}"

    # Example of posting text. To post video, you would need to generate a video file.
    post_to_facebook_page(FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN, post_message)

    print("Pipeline finished successfully.")


if __name__ == "__main__":
    # Ensure API keys are set
    if "YOUR_YOUTUBE_API_KEY" in YOUTUBE_API_KEY or "YOUR_FACEBOOK_ACCESS_TOKEN" in FACEBOOK_ACCESS_TOKEN:
        print("Error: API keys are not set. Please update placeholder values or set environment variables.")
    else:
        main()
