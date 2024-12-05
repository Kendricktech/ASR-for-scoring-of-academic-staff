from rest_framework import serializers
from .models import AudioFile, TextPrompt

class TextPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextPrompt
        fields = ['id', 'text']

class AudioFileSerializer(serializers.ModelSerializer):
    text_prompt = TextPromptSerializer()  # Serialize the related TextPrompt

    class Meta:
        model = AudioFile
        fields = [
            'id',
            'audio_file', 
            'text_prompt', 
            'uploaded_at', 
            'quality', 
            'accent', 
            'gender', 
            'age_group',
            'background_noise_level',
            'speech_clarity_score',
            'recording_environment',
            'is_verified',
            'is_ml_processed'
        ]
