from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import TextPrompt,AudioFile

admin.site.register(TextPrompt)
admin.site.register(AudioFile)