from django_q.tasks import async_task
import librosa
import os
from django.conf import settings
from .models import AudioFile

def process_audio_file(audio_file_id):
    try:
        # Get the audio file instance
        audio_file = AudioFile.objects.get(id=audio_file_id)
        audio_path = os.path.join(settings.MEDIA_ROOT, audio_file.audio_file.name)

        # Load the audio file
        y, sr = librosa.load(audio_path, sr=None)

        # Extract metadata
        rms = librosa.feature.rms(y=y)
        avg_rms = float(rms.mean())  # Background noise level
        hnr = librosa.effects.harmonic(y).mean()  # Speech clarity
        recording_environment = 'quiet room' if avg_rms < 0.02 else 'noisy'

        # Save metadata to the database
        audio_file.background_noise_level = avg_rms
        audio_file.speech_clarity_score = hnr
        audio_file.recording_environment = recording_environment
        audio_file.is_ml_processed = True
        audio_file.save()

        return f"Audio file {audio_file_id} processed successfully."

    except Exception as e:
        return f"Error processing audio file {audio_file_id}: {str(e)}"
