import mimetypes
import ntpath
import os

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
# Create your views here.
from django.views import View

from core.core_handler import CoreHandler
from core.manipulate_csv_file import CSVJSON
from core.tasks import verify_email_list
from email_verifer.settings import BASE_DIR, USE_CELERY


class HomeView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context_dict = {}
        self.core_obj = CoreHandler()

    def get(self, request):
        self.context_dict['all_file_uploads'] = self.core_obj.get_all_file_uploads()
        self.context_dict['processing_upload_exists'] = self.core_obj.update_upload_status()

        return render(request, 'index.html', self.context_dict)

    def post(self, request):
        file = request.FILES.get('the_file')

        csv_file = self.core_obj.create_file({'csv_file': file})
        csv_json = CSVJSON(csv_file.csv_file.url[1:])
        new_dict_list = csv_json.to_json()
        if request.POST.get('combinations-csv-file'):
            new_dict_list = csv_json.add_email_from_name_combinations()
        self.core_obj.add_json_data_to_file({'dict_list': new_dict_list, 'file_id': csv_file.id})
        if USE_CELERY:
            task = verify_email_list.delay(new_dict_list)
            self.core_obj.add_task_id_to_file({'file_id': csv_file.id, 'task_id': task.id})
            messages.success(request, 'The csv file was uploaded successfully. Processing has begun.')
        else:
            data_list = verify_email_list(new_dict_list)
            csv_file_output_path = csv_json.convert_dict_to_csv(data_list)
            self.core_obj.add_json_file_to_file_object(
                {'csv_file_id': csv_file.id, 'csv_file_output_path': csv_file_output_path})
            messages.success(request, 'The csv file was uploaded and processed successfully. The file is ready for '
                                      'download.')
        return redirect('home')


class DownloadReportView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context_dict = {}
        self.core_obj = CoreHandler()

    def get(self, request, file_id):
        file_location = self.core_obj.get_file_by_id({'file_id': file_id}).output_file.url[1:]
        file_name = ntpath.basename(os.path.join(BASE_DIR, file_location))
        file_location = file_location.replace('%20', ' ')
        with open(file_location, 'rb') as fh:
            mime_type, _ = mimetypes.guess_type(file_location)
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = 'attachment;filename=%s' % file_name
            return response


class CheckUploadStatusJSONView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context_dict = {}
        self.core_obj = CoreHandler()

    def get(self, request):
        processing_upload_exists = self.core_obj.update_upload_status()
        data_list = self.core_obj.check_upload_status()
        return JsonResponse({'data_list': data_list, 'processing_upload_exists': processing_upload_exists}, safe=False)
