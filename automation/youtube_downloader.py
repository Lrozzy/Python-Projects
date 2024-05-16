# definitely works in Jarvis env, probably need to add pytube and pydub to automation environment

from pytube import YouTube
from pydub import AudioSegment
import os

# Function to download audio from YouTube and convert it to .wav
def download_youtube_audio(youtube_url, output_filename):
    # Download video with only audio stream
    yt = YouTube(youtube_url)
    # Filter for only audio streams and prefer higher bitrate if available
    streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
    best_audio = streams.first()
    best_audio.download()
    
    # Convert the downloaded .webm file to .wav using pydub
    webm_audio = AudioSegment.from_file(r"C:\Users\leoro\OneDrive\Coding Practice\python_projects\JARVIS TIKTOK PC SOUND FREE HIGH QUALITY  ACDC WINDOWS STARTUP SOUND.webm", format="webm")
    webm_audio.export(output_filename, format="wav")

    # Clean up the temporary .mp4 file
    os.remove(r"C:\Users\leoro\OneDrive\Coding Practice\python_projects\JARVIS TIKTOK PC SOUND FREE HIGH QUALITY  ACDC WINDOWS STARTUP SOUND.webm")

    print(f"Downloaded and converted to .wav: {output_filename}")

youtube_url = "https://www.youtube.com/watch?v=5Vt7QvMdsNA"
output_filename = r"C:\Users\leoro\Downloads\jarvis_startup_sound.wav"
download_youtube_audio(youtube_url, output_filename)
