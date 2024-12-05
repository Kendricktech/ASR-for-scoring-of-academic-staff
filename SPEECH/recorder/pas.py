import requests
import os
import logging
import numpy as np
from pathlib import Path
from pydub import AudioSegment
import soundfile as sf
import librosa
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Server configuration
SERVER_URL = "http://127.0.0.1:8000"  # Replace with your actual server URL
GET_AUDIO_URL = f"{SERVER_URL}/api/audio_files/"  # Endpoint to fetch audio and text data
POST_METADATA_URL = f"{SERVER_URL}/api/update_metadata/"  # Endpoint to upload processed metadata

def json_serialize(obj):
    """Custom JSON serializer to handle NumPy types."""
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def fetch_audio_files():
    """Fetch audio files along with their associated text prompt labels."""
    try:
        response = requests.get(GET_AUDIO_URL)
        response.raise_for_status()
        return response.json()  # Expected to return audio data with text prompt labels
    except requests.RequestException as e:
        logger.error(f"Error fetching audio files: {e}")
        return []

def download_audio_file(url, output_dir):
    """Download audio file to the local system."""
    try:
        # Validate and construct full URL
        if not url.startswith(("http://", "https://")):
            url = f"{SERVER_URL}{url}" if not url.startswith("/") else f"{SERVER_URL}{url}"
        
        local_path = Path(output_dir) / os.path.basename(url)
        
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        logger.info(f"Downloaded file: {local_path}")
        return local_path
    except requests.RequestException as e:
        logger.error(f"Failed to download file {url}: {e}")
        return None

def process_audio(file_path):
    """Process the audio file to convert, trim, and extract metadata."""
    try:
        file_path = Path(file_path).resolve()
        wav_path = convert_to_wav(file_path)
        trimmed_path = trim_silence(wav_path)
        metadata = extract_audio_metadata(trimmed_path)
        return metadata
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return {}

def convert_to_wav(input_path):
    """Convert audio file to WAV using Pydub."""
    output_path = input_path.with_suffix(".wav")
    if input_path.suffix.lower() != '.wav':
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
    return output_path

def trim_silence(wav_path):
    """Trim silence from the start and end of a WAV file using librosa."""
    try:
        y, sr = librosa.load(wav_path, sr=None)
        y_trimmed, _ = librosa.effects.trim(y, top_db=30)
        trimmed_path = wav_path.with_name(wav_path.stem + '_trimmed.wav')
        sf.write(trimmed_path, y_trimmed, sr)
        return trimmed_path
    except Exception as e:
        logger.error(f"Error trimming silence from {wav_path}: {e}")
        return wav_path

def extract_audio_metadata(wav_path):
    """Extract metadata from the WAV file."""
    try:
        y, sr = librosa.load(wav_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        rms = float(librosa.feature.rms(y=y).mean())
        clarity_score = min(max(rms / 0.1, 0), 1)
        noise_level = float(librosa.feature.rms(y=y).mean())
        
        return {
            "Duration (seconds)": round(duration, 2),
            "RMS (Root Mean Square Energy)": round(rms, 4),
            "Speech Clarity Score": round(clarity_score, 2),
            "Background Noise Level": round(noise_level, 4),
        }
    except Exception as e:
        logger.error(f"Error extracting metadata from {wav_path}: {e}")
        return {}

def save_audio_with_metadata(file_path, metadata, text_prompt, output_dir):
    """Save the audio file along with its metadata and text prompt label."""
    try:
        audio_filename = Path(file_path).name
        metadata_filename = Path(file_path).stem + '_metadata.json'
        
        # Save the metadata as a JSON file
        metadata_path = Path(output_dir) / metadata_filename
        with open(metadata_path, 'w') as f:
            json.dump({
                "text_prompt": text_prompt,
                "metadata": metadata
            }, f, indent=4)
        
        # Save the audio file (the trimmed version)
        trimmed_audio_path = Path(output_dir) / audio_filename
        if not trimmed_audio_path.exists():
            Path(file_path).rename(trimmed_audio_path)
        
        logger.info(f"Saved audio and metadata: {trimmed_audio_path}, {metadata_path}")
        return trimmed_audio_path, metadata_path
    except Exception as e:
        logger.error(f"Error saving audio or metadata: {e}")
        return None, None

def upload_metadata(metadata_list):
    """Upload metadata back to the server."""
    try:
        response = requests.post(
            POST_METADATA_URL, 
            json=metadata_list,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        logger.info("Metadata uploaded successfully.")
    except requests.RequestException as e:
        logger.error(f"Error uploading metadata: {e}")
        logger.error(f"Metadata details: {metadata_list}")

def main():
    audio_files = fetch_audio_files()
    if not audio_files:
        logger.info("No unprocessed audio files found.")
        return
    
    output_dir = "processed_audio"
    os.makedirs(output_dir, exist_ok=True)
    
    metadata_list = []
    for audio in audio_files:
        url = audio['audio_file']
        text_prompt = audio['text_prompt']  # Assuming text prompt is part of the response
        file_path = download_audio_file(url, output_dir)
        if file_path:
            metadata = process_audio(file_path)
            if metadata:
                # Save audio and its metadata
                audio_path, metadata_path = save_audio_with_metadata(file_path, metadata, text_prompt, output_dir)
                if audio_path and metadata_path:
                    metadata_list.append({
                        "audio_file": audio_path,
                        "metadata_file": metadata_path,
                        "text_prompt": text_prompt,
                        "metadata": metadata
                    })
    
    if metadata_list:
        upload_metadata(metadata_list)

if __name__ == "__main__":
    main()
