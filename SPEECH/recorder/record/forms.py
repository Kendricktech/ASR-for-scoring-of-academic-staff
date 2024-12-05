# forms.py
from django import forms
from .models import AudioFile

class AudioFileForm(forms.ModelForm):
    class Meta:
        model = AudioFile
        fields = ['text_prompt', 'audio_file']

    # Add custom validation if needed
    def clean_audio_file(self):
        audio_file = self.cleaned_data.get('audio_file')
        if not audio_file:
            raise forms.ValidationError("Please upload an audio file.")
        return audio_file
