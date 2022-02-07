from django.contrib import admin

# Register your models here.
from core.models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['id', 'csv_file', 'start_processing_time', 'stop_processing_time', 'status',
                    ]
