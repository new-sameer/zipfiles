from django.urls import path

from core.views import HomeView, DownloadReportView, CheckUploadStatusJSONView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('download/<int:file_id>/', DownloadReportView.as_view(), name='download'),
    path('check_upload_status', CheckUploadStatusJSONView.as_view(), name='check_upload_status'),
]
