# Works with jarvis env, but probably not with autovenv

import os
import subprocess
import shutil
import threading # New import
import time # New import
import psutil # New import
from pytubefix import YouTube, Playlist
from pydub import AudioSegment
from tqdm import tqdm

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
# download_youtube_audio(youtube_url, output_filename)

# Function to check if ffmpeg is installed and in PATH
def is_ffmpeg_installed():
    return shutil.which("ffmpeg") is not None

# Global variables for inter-thread communication and progress bars
terminate_ffmpeg = False
ffmpeg_process = None
pbar_download = None

def monitor_ram(process, available_ram_threshold_bytes, check_interval=2):
    """Monitors available system RAM and terminates the process if it drops below threshold."""
    global terminate_ffmpeg
    terminate_ffmpeg = False # Reset flag for each new process
    # print(f"\nMonitoring RAM: Target available > {available_ram_threshold_bytes / (1024**3):.2f} GB.") # Debug print
    while process.poll() is None: # While process is running
        try:
            available_ram = psutil.virtual_memory().available
            if available_ram < available_ram_threshold_bytes:
                print(f"\nRAM Alert! Available RAM ({available_ram / (1024**3):.2f} GB) below threshold ({available_ram_threshold_bytes / (1024**3):.2f} GB). Terminating ffmpeg...")
                try:
                    # Send terminate signal (graceful shutdown)
                    process.terminate()
                    # Wait a bit for graceful termination
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                         # Force kill if terminate didn't work
                        print("ffmpeg did not terminate gracefully, forcing kill.")
                        process.kill()
                    terminate_ffmpeg = True # Signal that we initiated termination
                    print("ffmpeg process terminated due to low RAM.")
                except psutil.NoSuchProcess:
                     print("ffmpeg process already finished or couldn't be found when trying to terminate.")
                except Exception as e:
                    print(f"Error terminating ffmpeg process: {e}")
                break # Exit monitoring loop
        except Exception as e:
            print(f"\nError in RAM monitoring thread: {e}")
            # Decide if the monitor should stop on error or continue
            break # Stop monitoring on error
        time.sleep(check_interval)
    # print("RAM monitoring stopped.") # Optional: signal monitor exit


# pytubefix progress callback function
def on_progress(stream, chunk, bytes_remaining):
    """Callback function for pytubefix download progress, updates tqdm bar."""
    global pbar_download
    if pbar_download:
        pbar_download.update(len(chunk)) # Update the download bar by the chunk size


def download_playlist_audio(playlist_url, output_folder, max_ram_gb_available=2.0):
    """
    Download audio from YouTube playlist, convert using ffmpeg, with progress bars and RAM monitoring.
    :param playlist_url: URL of the YouTube playlist.
    :param output_folder: Folder to save MP3 files.
    :param max_ram_gb_available: If available system RAM drops below this value (in GB), stop ffmpeg conversion.
    """
    global pbar_download, terminate_ffmpeg, ffmpeg_process

    if not is_ffmpeg_installed():
        print("Error: ffmpeg is not installed or not found in PATH. Please install ffmpeg.")
        return

    try:
        pl = Playlist(playlist_url)
        # Fetch URLs immediately to get accurate count for tqdm
        video_urls = list(pl.video_urls) # Convert generator to list
        print(f"Found {len(video_urls)} videos in playlist.")
    except Exception as e:
        print(f"Error fetching playlist details for {playlist_url}: {e}")
        return

    os.makedirs(output_folder, exist_ok=True)
    available_ram_threshold_bytes = max_ram_gb_available * (1024**3)

    # Overall playlist progress bar
    pbar_playlist = tqdm(total=len(video_urls), unit='video', desc="Playlist Progress")

    for i, url in enumerate(video_urls):
        terminate_ffmpeg = False # Reset termination flag for each video
        temp_file_path = None # Ensure temp_file_path is defined in scope
        monitor_thread = None
        ffmpeg_process = None # Reset ffmpeg process for the loop
        pbar_download = None # Reset download progress bar

        try:
            yt = YouTube(url)
            # Register progress callback *before* accessing streams/downloading
            yt.register_on_progress_callback(on_progress)

            # Sanitize title for filename
            base_title = ''.join(c for c in yt.title if c.isalnum() or c in (' ', '_', '-')).rstrip().strip()
            if not base_title: # Handle cases where title becomes empty after sanitizing
                base_title = f"video_{i+1}"
            pbar_playlist.set_description(f"Playlist ({base_title[:30]}...)") # Update description

            streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
            best_audio = streams.first()
            if not best_audio:
                tqdm.write(f"\n[{i+1}/{len(video_urls)}] No audio stream found for {url}. Skipping.") # Use tqdm.write
                pbar_playlist.update(1) # Update overall progress
                continue

            # --- Download Step ---
            tqdm.write(f"\n[{i+1}/{len(video_urls)}] Downloading: {base_title}") # Use tqdm.write for messages
            # Setup download progress bar for this file
            pbar_download = tqdm(total=best_audio.filesize, unit='B', unit_scale=True, desc="Download", leave=False, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
            # Download to a temporary file
            temp_file_path = best_audio.download(output_path=output_folder, filename_prefix="temp_dl_", skip_existing=False) # Use prefix
            if pbar_download: pbar_download.close() # Close download bar

            # --- Conversion Step ---
            mp3_filename = os.path.join(output_folder, f"{base_title}.mp3")
            tqdm.write(f"Converting to MP3: {os.path.basename(mp3_filename)}") # Use tqdm.write

            cmd = [
                'ffmpeg',
                '-i', temp_file_path,
                '-vn',           # No video
                '-ab', '192k',   # Set audio bitrate
                '-ar', '44100',  # Set audio sampling rate
                '-f', 'mp3',     # Output format
                '-y',            # Overwrite output
                mp3_filename
            ]

            # Use Popen instead of run to allow monitoring
            # Redirect stderr to PIPE to capture potential ffmpeg errors, hide stdout unless needed
            ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')

            # Start RAM monitoring thread
            monitor_thread = threading.Thread(target=monitor_ram, args=(ffmpeg_process, available_ram_threshold_bytes), daemon=True)
            monitor_thread.start()

            # Wait for ffmpeg process to complete (or be terminated)
            # Capture stderr while waiting
            _, stderr = ffmpeg_process.communicate()

            # Wait for monitor thread to finish its last check (optional, but good practice)
            if monitor_thread: monitor_thread.join(timeout=5) # Give it a few seconds to finish

            # Check if terminated by monitor or ffmpeg error
            if terminate_ffmpeg:
                 tqdm.write(f"Conversion stopped for {base_title} due to low RAM.") # Use tqdm.write
                 # Clean up partially converted file if it exists
                 if os.path.exists(mp3_filename):
                     try: os.remove(mp3_filename)
                     except OSError as e: tqdm.write(f"Could not remove partial mp3 {mp3_filename}: {e}")
                 # Keep the temp file? Or remove it? Let's remove it.
                 # Temp file is removed in finally block now

                 # Optionally, break the loop entirely if one fails due to RAM? Or continue? Let's continue.
                 # continue # Skip to finally block via normal loop end

            elif ffmpeg_process.returncode != 0:
                tqdm.write(f"\nffmpeg error during conversion for {base_title} (Return Code: {ffmpeg_process.returncode})") # Use tqdm.write
                if stderr: tqdm.write(f"ffmpeg stderr:\n{stderr[:1000]}...") # Show first part of error
                # Clean up potentially corrupted mp3
                if os.path.exists(mp3_filename):
                     try: os.remove(mp3_filename)
                     except OSError as e: tqdm.write(f"Could not remove failed mp3 {mp3_filename}: {e}")
            else:
                tqdm.write(f"Successfully saved: {os.path.basename(mp3_filename)}") # Use tqdm.write

        except Exception as e:
            tqdm.write(f"\nError processing {url} ({base_title if 'base_title' in locals() else 'N/A'}): {e}") # Use tqdm.write
            # Attempt to kill ffmpeg if it's still running on general error
            if ffmpeg_process and ffmpeg_process.poll() is None:
                try:
                    tqdm.write("Attempting to kill lingering ffmpeg process on error...")
                    ffmpeg_process.kill()
                    ffmpeg_process.wait(timeout=5) # Wait for kill
                except Exception as kill_e:
                    tqdm.write(f"Could not kill lingering ffmpeg process: {kill_e}")
            # Cleanup potentially incomplete mp3 on error
            if 'mp3_filename' in locals() and os.path.exists(mp3_filename):
                 # Check return code again, maybe error happened after successful conversion?
                 # If ffmpeg_process exists and returncode is 0, don't delete.
                 should_delete = True
                 if ffmpeg_process and ffmpeg_process.returncode == 0:
                     should_delete = False
                 if should_delete:
                     try:
                         os.remove(mp3_filename)
                         tqdm.write(f"Removed potentially incomplete file {mp3_filename} on error.")
                     except OSError as e: tqdm.write(f"Could not remove mp3 {mp3_filename} on error: {e}")

        finally:
             # Ensure temporary download file is always removed if it exists
             if temp_file_path and os.path.exists(temp_file_path):
                 try:
                     os.remove(temp_file_path)
                 except OSError as e:
                     tqdm.write(f"Could not remove temporary file {temp_file_path}: {e}") # Use tqdm.write
             # Ensure playlist progress bar is updated
             pbar_playlist.update(1)
             # Ensure download bar is closed if it exists and wasn't closed
             if pbar_download and hasattr(pbar_download, 'close') and not pbar_download.disable:
                 try: pbar_download.close()
                 except: pass # Ignore errors closing already closed bar


    pbar_playlist.close()
    print("\nPlaylist processing finished.")


# Example usage:
playlist_url = r"https://www.youtube.com/playlist?list=PLSN2-xRPTOu83Vj3twSkOaMohDhaTOWMM"
output_folder = r"C:\Users\leoro\OneDrive\Obsidian_music"
download_playlist_audio(playlist_url, output_folder, max_ram_gb_available=3.0) # Stop if less than 4GB RAM available