from django.urls import path
from .views import RecordAudioView, RecordListView, TextPromptAudioFilesView,process_audio_view,AudioFileListView,UpdateAudioMetadataView

urlpatterns = [
    path('', RecordAudioView.as_view(), name='record_audio'),
    path('list', RecordListView.as_view(), name='audio_files'),
        path('process-audio/', process_audio_view, name='process_audio'),

    path('text_prompt/<int:text_id>/audio_files/', TextPromptAudioFilesView.as_view(), name='text_prompt_audio_files'),
     path('api/audio_files/', AudioFileListView.as_view(), name='audio_files'),

    # Endpoint to update metadata
    path('api/update_metadata/', UpdateAudioMetadataView.as_view(), name='update_metadata')
]
