from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import TextPrompt, AudioFile
import random
import logging

logger = logging.getLogger(__name__)

class RecordAudioView(View):
    def get(self, request, *args, **kwargs):
        """Handle GET requests: select a random text prompt"""
        text_prompt = random.choice(TextPrompt.objects.all()) if TextPrompt.objects.exists() else None

        if not text_prompt:
            messages.error(request, "No text prompts available.")
            return redirect('home')  # Adjust this to an appropriate redirect

        return render(request, 'record_audio.html', {'text_prompt': text_prompt})

    def post(self, request, *args, **kwargs):
        """Handle POST requests: save uploaded audio file"""
        text_id = request.POST.get('text_id')
        audio_file = request.FILES.get('audio_file')

        logger.info(f"Received POST request: text_id={text_id}")
        logger.info(f"Audio file received: {audio_file}")

        if not text_id:
            messages.error(request, "No text prompt selected.")
            return redirect('record_audio')

        if not audio_file:
            messages.error(request, "No audio file was uploaded.")
            return redirect('record_audio')

        try:
            text_prompt = TextPrompt.objects.get(id=text_id)
        except TextPrompt.DoesNotExist:
            messages.error(request, "Invalid text prompt.")
            return redirect('record_audio')

        try:
            # Create the AudioFile instance
            audio_file_instance = AudioFile(
                text_prompt=text_prompt,
                audio_file=audio_file
            )

            # Save the instance to the database
            audio_file_instance.save()

            messages.success(request, "Audio file uploaded successfully!")
        
        except Exception as e:
            messages.error(request, f"Error saving audio file: {str(e)}")
            logger.error(f"Error saving audio file: {str(e)}")
            return redirect('record_audio')

        return redirect('record_audio')

from django.views.generic import ListView
from .models import AudioFile

class RecordListView(ListView):
    model = AudioFile
    template_name = 'list.html'
    context_object_name = 'audio_files'  # The context object will be accessible as `audio_files` in the template

    # You can customize the queryset if necessary
    def get_queryset(self):
        return AudioFile.objects.all()

from django.views import View
from django.shortcuts import render
from .models import TextPrompt

class TextPromptAudioFilesView(View):
    def get(self, request, text_id, *args, **kwargs):
        try:
            text_prompt = TextPrompt.objects.get(id=text_id)
            audio_files = text_prompt.audio_files.all()  # Access related audio files
        except TextPrompt.DoesNotExist:
            messages.error(request, "Text prompt not found.")
            return redirect('home')

        return render(request, 'text_prompt_audio_files.html', {
            'text_prompt': text_prompt,
            'audio_files': audio_files,
        })
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

import os
import librosa
import soundfile as sf
import subprocess
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from record.models import AudioFile  # Replace with your actual app model

def process_audio_view(request):
    """
    View to process audio files by converting to WAV, trimming silence,
    and extracting metadata.
    """
    try:
        # Get all unprocessed audio files
        unprocessed_files = AudioFile.objects.all()

        if not unprocessed_files.exists():
            return JsonResponse({"message": "No unprocessed audio files found."}, status=200)

        # Process each audio file
        for audio_file in unprocessed_files:
            with transaction.atomic():
                process_audio_file(audio_file)

        return JsonResponse({"message": "Audio files processed successfully."}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def process_audio_file(audio_file):
    """Processes a single audio file: convert to WAV, trim silence, and extract metadata."""
    try:
        # Use absolute paths and ensure directory exists
        original_path = Path(audio_file.audio_file.path).resolve()
        media_root = Path(settings.MEDIA_ROOT)  # Import settings at the top of your file
        
        # Ensure the directory exists for converted and trimmed files
        converted_dir = original_path.parent
        converted_path = converted_dir / f"{original_path.stem}.wav"
        
        # Convert to WAV (if needed)
        if original_path.suffix.lower() != '.wav':
            convert_to_wav(original_path, converted_path)
            
            # Update file path relative to MEDIA_ROOT
            relative_path = converted_path.relative_to(media_root)
            audio_file.audio_file.name = str(relative_path)
            audio_file.save(update_fields=['audio_file'])

        # Trim silence
        trimmed_path = trim_silence(converted_path)

        # Process the trimmed WAV file
        extract_audio_metadata(audio_file, trimmed_path)

        # Clean up intermediate files 
        if converted_path.exists():
            converted_path.unlink()
        if trimmed_path.exists():
            trimmed_path.unlink()

    except Exception as e:
        logger.error(f"Error processing {audio_file.audio_file.name}: {str(e)}")
        raise


def convert_to_wav(input_path, output_path):
    """Convert any input audio format to WAV using ffmpeg."""
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run([
            'ffmpeg', 
            '-i', str(input_path),  # Convert Path to string
            '-acodec', 'pcm_s16le', 
            '-ar', '44100', 
            '-ac', '1', 
            str(output_path)  # Convert Path to string
        ], check=True, stderr=subprocess.PIPE)

    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg conversion error for {input_path}: {error_message}")
        raise

def trim_silence(wav_path):
    """Trim silence from the start and end of a WAV file using librosa."""
    try:
        y, sr = librosa.load(wav_path, sr=None)
        y_trimmed, _ = librosa.effects.trim(y, top_db=30)  # Adjust top_db as needed
        trimmed_path = wav_path.with_stem(wav_path.stem + '_trimmed')
        sf.write(trimmed_path, y_trimmed, sr)  # Save trimmed audio
        return trimmed_path
    except Exception as e:
        raise Exception(f"Error trimming silence from {wav_path}: {str(e)}")


def extract_audio_metadata(audio_file, wav_path):
    """Extracts audio metadata and updates the database."""
    try:
        y, sr = librosa.load(wav_path, sr=None)

        # Example metadata extraction
        duration = librosa.get_duration(y=y, sr=sr)
        rms = librosa.feature.rms(y=y).mean()
        clarity_score = min(max(rms / 0.1, 0), 1)  # Normalize clarity score
        noise_level = librosa.feature.rms(y=y[y < 0.01]).mean()

        # Update metadata fields
        audio_file.speech_clarity_score = round(clarity_score, 2)
        audio_file.background_noise_level = round(noise_level, 2)
        audio_file.is_ml_processed = True
        audio_file.save()

    except Exception as e:
        raise Exception(f"Error extracting metadata from {wav_path}: {str(e)}")


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AudioFile
from .serializers import AudioFileSerializer
import logging

logger = logging.getLogger(__name__)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AudioFile
from .serializers import AudioFileSerializer

class AudioFileListView(APIView):
    """
    API View to retrieve all unprocessed audio files along with their metadata.
    """
    def get(self, request, *args, **kwargs):
        # Retrieve all AudioFile objects
        unprocessed_files = AudioFile.objects.all()

        # Serialize the audio files along with their associated metadata
        serializer = AudioFileSerializer(unprocessed_files, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateAudioMetadataView(APIView):
    """
    API View to receive metadata updates and save them to the database.
    """
    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            for record in data:
                audio_id = record.get("id")
                metadata = record.get("metadata", {})
                
                audio_file = AudioFile.objects.get(id=audio_id)
                audio_file.speech_clarity_score = metadata.get("Speech Clarity Score", 0)
                audio_file.background_noise_level = metadata.get("Background Noise Level", 0)
                audio_file.is_ml_processed = True
                audio_file.save()

            return Response({"message": "Metadata updated successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error updating metadata: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
