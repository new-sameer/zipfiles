import datetime
import logging
import random
import string
import traceback

import pytz
from celery.result import AsyncResult
from django.core.files import File as DjangoFile
from django.db import models
# Create your models here.
from django.urls import reverse

from config_master import file_status_choices, STATUS_UPLOADED, STATUS_PROCESSING, STATUS_COMPLETED
from core.manipulate_csv_file import CSVJSON
from email_verifer.settings import TIME_ZONE

log = logging.getLogger(__name__)
tz = pytz.timezone(TIME_ZONE)


class File(models.Model):
    csv_file = models.FileField(null=False, upload_to='json_upload_files')
    json_data = models.JSONField(default=dict)
    start_processing_time = models.DateTimeField(null=True, blank=True)
    stop_processing_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=file_status_choices, default=STATUS_UPLOADED, null=True,
                              blank=True)
    output_file = models.FileField(null=True, blank=True, upload_to='output_file')
    task_id = models.CharField(max_length=100, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)


class CoreManager:
    def add_json_data_to_file(self, data):
        """
        This function adds json data to a file object
        :param data: {"dict_list': A list of dictionaries containing data,'file_id': The Id value of the file}
        :return:
        """
        file = File.objects.get(id=data.get('file_id'))
        file.json_data = data.get('dict_list')
        file.save()
        return file

    def randomword(self, length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def create_file(self, data):
        """
        This function creates a new instance of a file object
        :param data: {'csv_file': The json_file object}
        :return:
        """
        return File.objects.create(csv_file=data.get('csv_file'))

    def get_file_by_id(self, data):
        return File.objects.get(id=data.get('file_id'))

    def add_task_id_to_file(self, data):
        """
        This function assign a task id from a celery task to a file object
        :param data: {'task_id': The Task ID value from a celery task, 'file_id': The ID value of the file}
        :return:
        """
        file = File.objects.get(id=data.get('file_id'))
        file.task_id = data.get('task_id')
        file.start_processing_time = datetime.datetime.now(tz=tz)
        file.status = STATUS_PROCESSING
        file.save()
        return file

    def get_all_file_uploads(self):
        """
        This function returns file uploads that contain a task id
        :return:
        """
        return File.objects.all().order_by('-id')

    def add_json_file_to_file_object(self, data):
        file = File.objects.get(id=data.get('csv_file_id'))
        local_file = open(data.get('csv_file_output_path'), 'rb')
        djangofile = DjangoFile(local_file)
        file.output_file.save(f'{self.randomword(30)}.csv', djangofile)
        file.status = STATUS_COMPLETED
        file.start_processing_time = datetime.datetime.now(tz)
        file.stop_processing_time = datetime.datetime.now(tz)
        file.save()
        return file

    def update_upload_status(self):
        """
        This function updates the status of file uploads
        :return:
        """
        all_processing_file_uploads = File.objects.filter(status=STATUS_PROCESSING)
        for file_upload in all_processing_file_uploads:
            res = AsyncResult(file_upload.task_id)
            if res.ready():
                try:
                    data_list = res.get()
                    csv_json = CSVJSON(file_upload.csv_file.url[1:])
                    csv_file_output_path = csv_json.convert_dict_to_csv(data_list)
                    local_file = open(csv_file_output_path, 'rb')
                    djangofile = DjangoFile(local_file)
                    file_upload.output_file.save(f'{self.randomword(30)}.csv', djangofile)
                    file_upload.stop_processing_time = datetime.datetime.now(tz)
                    file_upload.save()

                    if file_upload.output_file:
                        file_upload.status = STATUS_COMPLETED
                    else:
                        file_upload.status = STATUS_PROCESSING
                    file_upload.save()
                except:
                    logging.error(traceback.format_exc())


            else:
                continue
        return File.objects.filter(status=STATUS_PROCESSING).exists()

    def check_upload_status(self):
        """
        This function check all upload items and checks their upload status
        :return:
        """
        all_file_uploads = File.objects.all().order_by('-id')
        all_file_upload_details = []
        for file_upload in all_file_uploads:
            try:
                if file_upload.output_file:
                    download_url = reverse('download', kwargs={'file_id': file_upload.id})
                else:
                    download_url = '#'
                all_file_upload_details.append(
                    {
                        'id': file_upload.id,
                        'json_file': file_upload.csv_file.name,
                        'start_processing_time': file_upload.start_processing_time,
                        'status': file_upload.status,
                        'download_url': download_url,
                        'created_on': file_upload.created_on.strftime("%b,%d,%Y,%H:%M:%S"),
                    }
                )

            except Exception:
                logging.error(traceback.format_exc())
                continue
        return all_file_upload_details
