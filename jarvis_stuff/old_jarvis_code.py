def create_stream():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,  # 16-bit PCM
                    channels=1,  # mono
                    rate=16000,  # Sample rate
                    input=True,
                    frames_per_buffer=320)  # Frame size
    time.sleep(1)  # Delay for 1 second to let the mic stabilize
    return stream, p

def detect_audio():
    vad = webrtcvad.Vad(2)  # Set aggressiveness level
    stream, p = create_stream()
    r = sr.Recognizer()
    print("Listening...")
    active = False
    frames = []
    discard_frames = 20  # Number of initial frames to discard
    pause_length = 20  # Number of frames to consider as pause

    while True:
        frame = stream.read(320, exception_on_overflow=False)  # Read a frame
        if discard_frames > 0:
            discard_frames -= 1
            continue  # Skip processing for the first few frames

        is_speech = vad.is_speech(frame, 16000)  # Check if the frame is speech
        if not active:
            if is_speech:
                active = True  # Start of speech detected
                frames.append(frame)
        else:
            frames.append(frame)  # Continue appending frames if already active
            if not is_speech:
                # If non-speech is detected, assume it might be a pause
                pause_duration = sum(1 for _ in range(pause_length) if not vad.is_speech(stream.read(320), 16000))
                if pause_duration >= pause_length:  # Adjust this threshold based on your testing
                    # End of speech detected, process the collected frames
                    audio_data = b''.join(frames)
                    audio = sr.AudioData(audio_data, 16000, 2)
                    try:
                        text = r.recognize_google(audio, language="en-GB")
                        if "stop" in text.lower() or "shutdown" in text.lower():
                            response_text = random.choice(shutdown_messages)
                            speak_text(response_text)
                            print(response_text)
                            break
                        print("You said:", text)
                        return text
                    except sr.UnknownValueError:
                        print("Google Speech Recognition could not understand audio")
                    except sr.RequestError as e:
                        print("Could not request results from Google Speech Recognition service;", e)
                    
                    # Reset for the next speech detection
                    active = False
                    frames = []
                    print("Listening...")


import pafy, pyglet
import urllib.request
from urllib.parse import *
import lxml
from bs4 import BeautifulSoup
import re


class Youtube_mp3():
    def __init__(self):
        self.lst = []
        self.dict = {}
        self.dict_names = {}
        self.playlist = []

    def url_search(self, search_string, max_search):
        textToSearch = search_string
        query = quote(textToSearch)
        url = f"https://www.youtube.com/results?search_query={query}"
        print(url)
        response = urllib.request.urlopen(url)
        html = response.read().decode('utf-8')  # Decode the bytes to a string

        # Regular expression to find video IDs in the JSON data
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        unique_video_ids = set(video_ids)  # Using a set to eliminate duplicates

        i = 1
        for video_id in unique_video_ids:
            if len(self.dict) < max_search:
                video_url = f'https://www.youtube.com/watch?v={video_id}'
                self.dict[i] = video_url
                print(f"Added {video_url}")  # Debugging output to check URLs being added
                i += 1
            else:
                break

    def play_media(self, query):
        # Initialize YouTube object with the URL
        yt = YouTube(self.dict[int(num)])
        
        # Filter for only audio streams and prefer higher bitrate if available
        streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
        
        # Select the best audio stream (highest bitrate)
        best_audio = streams.first()
        
        # Define the filename
        filename = 'song.m4a'
        
        # Download the audio file
        best_audio.download(output_path=None, filename=filename)
        
        # Load and play the audio file using pyglet
        song = pyglet.media.load(filename)
        player = pyglet.media.Player()
        player.queue(song)
        print("Playing")
        player.play()
        
        # Control loop for play, pause, or stop
        stop = ''
        while True:
            stop = input('Type "s" to stop; "p" to pause; "" to play; : ')
            if stop == 's':
                player.pause()
                # Delete the file after stopping the playback
                try:
                    os.remove(filename)
                    # print("File deleted successfully")
                except OSError as e:
                    print(f"Error: {e.strerror}")
                break
            elif stop == 'p':
                player.pause()
            elif stop == '':
                player.play()


if __name__ == '__main__':
    print('Welcome to the Youtube-Mp3 player.')
    x = Youtube_mp3()
    search = ''
    while search != 'q':
        search = input("Youtube Search: ")
        old_search = search
        max_search = 5
        # if search == '':
        #     print('\nFetching for: {0} on youtube.'.format(old_search.title()))
        #     x.url_search(search, max_search)
        #     x.get_search_items(max_search)
        #     song_number = input('Input song number: ')
        #     x.play_media(song_number)

        x.dict = {}
        x.dict_names = {}

        if search == 'q':
            print("Ending Youtube-Mp3 player.")
            break

        print('\nFetching for: {0} on youtube.'.format(search.title()))
        x.url_search(search, max_search)
        song_number = input('Input song number: ')
        x.play_media(song_number)
        
############################################################################################################
# Transcribing jarvis voice
# Directories
aif_dir = "Jarvis"
transcripts_dir = "jarvis_transcription_files"
max_retries = 3

# Create transcripts directory if it doesn't exist
os.makedirs(transcripts_dir, exist_ok=True)

# Initialize the recognizer
recognizer = sr.Recognizer()

# Function to transcribe a single audio file with retries
def transcribe_audio(audio_path, transcript_path):
    attempts = 0
    while attempts < max_retries:
        attempts += 1
        try:
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            # print(f"Attempt {attempts}: Could not understand audio in {os.path.basename(audio_path)}")
            x = 1
        except sr.RequestError as e:
            print(f"Attempt {attempts}: Could not request results from Google Speech Recognition service; {e}")
    return None

# Iterate through all .aif files in the jarvis_aif_files directory
for aif_file in os.listdir(aif_dir):
    if aif_file.endswith(".aif"):
        audio_path = os.path.join(aif_dir, aif_file)
        transcript_path = os.path.join(transcripts_dir, f"{os.path.splitext(aif_file)[0]}.txt")
        
        # Check if transcription already exists
        if os.path.exists(transcript_path):
            # print(f"Skipping {aif_file}, transcription already exists.")
            continue
        
        # Transcribe the audio file with retry logic
        transcription = transcribe_audio(audio_path, transcript_path)
        
        if transcription:
            print(f"Transcribed {aif_file}: {transcription}")
            with open(transcript_path, "w") as transcript_file:
                transcript_file.write(transcription)
        else:
            print(f"Failed to transcribe {aif_file} after {max_retries} attempts.")

# Initialize inflect engine for text conversion
p = inflect.engine()

# Function to create transcription for "caged_num_*"
def create_num_transcript(number):
    return p.number_to_words(number)

# Function to create transcription for "caged_date_*"
def create_date_transcript(number):
    return p.ordinal(p.number_to_words(number))

# Function to write transcript files
def write_transcript(filename, transcript_text):
    transcript_path = os.path.join(transcripts_dir, f"{filename}.txt")
    with open(transcript_path, "w") as transcript_file:
        transcript_file.write(transcript_text)

# Process "caged_num_*" files
for aif_file in os.listdir(aif_dir):
    if aif_file.startswith("caged_num_") and aif_file.endswith(".aif"):
        try:
            number = int(aif_file.split("_")[2].split(".")[0])
            transcript_text = create_num_transcript(number)
            write_transcript(os.path.splitext(aif_file)[0], transcript_text)
            print(f"Transcribed {aif_file} to '{transcript_text}'")
        except ValueError:
            print(f"Could not extract number from {aif_file}")

# Process "caged_date_*" files
for aif_file in os.listdir(aif_dir):
    if aif_file.startswith("caged_date_") and aif_file.endswith(".aif"):
        try:
            number = int(aif_file.split("_")[2].split(".")[0])
            transcript_text = create_date_transcript(number)
            write_transcript(os.path.splitext(aif_file)[0], transcript_text)
            print(f"Transcribed {aif_file} to '{transcript_text}'")
        except ValueError:
            print(f"Could not extract number from {aif_file}")

missing_files = []
for wav_file in os.listdir(wav_dir):
    if wav_file.endswith(".wav"):
        transcript_file = f"{os.path.splitext(wav_file)[0]}.txt"
        if not os.path.exists(os.path.join(transcripts_dir, transcript_file)):
            missing_files.append(wav_file)
            
print(len(missing_files))       
     
# Identify all .wav files in the jarvis directory
all_wav_files = [f for f in os.listdir(wav_dir) if f.endswith(".wav")]
# Calculate the total size of all .wav files
total_size_bytes = sum(os.path.getsize(os.path.join(wav_dir, f)) for f in all_wav_files)

# Calculate the size of missing .wav files
missing_size_bytes = sum(os.path.getsize(os.path.join(wav_dir, f)) for f in missing_files)

# Convert sizes to MB
total_size_mb = total_size_bytes / (1024 * 1024)
missing_size_mb = missing_size_bytes / (1024 * 1024)

# Print results
print(f"Missing audio size: {missing_size_mb:.2f} MB / Total audio size: {total_size_mb:.2f} MB")

# Parameters
total_transcribed_size_mb = 161.62 - 17.22  # Already transcribed audio size in MB
average_bitrate_kbps = 1411  # Example bitrate in kbps

# Convert MB to bits
total_transcribed_bits = total_transcribed_size_mb * 1024 * 1024 * 8

# Calculate total seconds and convert to hours
total_transcribed_seconds = total_transcribed_bits / (average_bitrate_kbps * 1000)
total_transcribed_hours = total_transcribed_seconds / 3600

print(f"Total Transcribed Hours: {total_transcribed_hours:.2f}")

############################################################################################################
# Clone Jarvis voice
url = "https://api.play.ht/api/v2/cloned-voices/instant"
jarvis_stuff_dir = r"C:\Users\leoro\OneDrive\Coding Practice\python_projects\jarvis_stuff\jarvis_wav_files"
os.chdir(jarvis_stuff_dir)
files = { "sample_file": ("caged_ringtone_call_0.wav", open("caged_ringtone_call_0.wav", "rb"), "audio/wavf") }
payload = { "voice_name": "Jarvis" }
headers = {
    "accept": "application/json",
    "AUTHORIZATION": "",
    "X-USER-ID": ""
}

response = requests.post(url, data=payload, files=files, headers=headers)

print(response.text)

# Check list of cloned voices from play.ht
url = "https://api.play.ht/api/v2/cloned-voices"

headers = {
    "accept": "application/json",
    "AUTHORIZATION": "",
    "X-USER-ID": ""
}

response = requests.get(url, headers=headers)

print(response.text)