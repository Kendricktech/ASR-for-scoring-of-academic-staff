import os
from django.db import models
from django.core.validators import FileExtensionValidator

def audio_file_path(instance, filename):
    return os.path.join('recordings', str(instance.text_prompt.id), filename)

class TextPrompt(models.Model):
    text = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.text

class AudioFile(models.Model):
    # Machine Learning Relevant Fields
    QUALITY_CHOICES = [
        ('high', 'High Quality'),
        ('medium', 'Medium Quality'),
        ('low', 'Low Quality')
    ]

    ACCENT_CHOICES = [
        ('neutral', 'Neutral'),
        ('american', 'American English'),
        ('british', 'British English'),
        ('australian', 'Australian English'),
        ('indian', 'Indian English'),
        ('other', 'Other Accent')
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]

    AGE_GROUP_CHOICES = [
        ('child', 'Child (0-12)'),
        ('teen', 'Teenager (13-19)'),
        ('young_adult', 'Young Adult (20-35)'),
        ('adult', 'Adult (36-55)'),
        ('senior', 'Senior (55+)')
    ]

    # Relationship and File Storage
    text_prompt = models.ForeignKey(
        TextPrompt,
        on_delete=models.CASCADE,
        related_name="audio_files"
    )
    audio_file = models.FileField(
        upload_to=audio_file_path,
        validators=[FileExtensionValidator(['wav', 'mp3', 'ogg'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Machine Learning Labeling Metadata
    quality = models.CharField(
        max_length=10, 
        choices=QUALITY_CHOICES, 
        null=True, 
        blank=True
    )
    accent = models.CharField(
        max_length=20, 
        choices=ACCENT_CHOICES, 
        null=True, 
        blank=True
    )
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        null=True, 
        blank=True
    )
    age_group = models.CharField(
        max_length=20, 
        choices=AGE_GROUP_CHOICES, 
        null=True, 
        blank=True
    )

    # Additional ML-relevant metadata
    background_noise_level = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Estimated background noise level (0-1)"
    )
    speech_clarity_score = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Speech clarity score (0-1)"
    )
    recording_environment = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="Recording environment (e.g., quiet room, outdoor, etc.)"
    )

    # Optional: Machine Learning Processing Flags
    is_verified = models.BooleanField(default=False)
    is_ml_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Audio for: {self.text_prompt.text} - {self.uploaded_at}"

    class Meta:
        ordering = ['-uploaded_at']