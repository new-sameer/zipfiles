from core.models import CoreManager


class CoreHandler:
    def __init__(self):
        self.core_obj = CoreManager()

    def get_file_by_id(self, data):
        return self.core_obj.get_file_by_id(data)

    def add_task_id_to_file(self, data):
        return self.core_obj.add_task_id_to_file(data)

    def get_all_file_uploads(self):
        return self.core_obj.get_all_file_uploads()

    def add_json_file_to_file_object(self, data):
        return self.core_obj.add_json_file_to_file_object(data)

    def update_upload_status(self):
        return self.core_obj.update_upload_status()

    def create_file(self, data):
        return self.core_obj.create_file(data)

    def add_json_data_to_file(self, data):
        return self.core_obj.add_json_data_to_file(data)

    def check_upload_status(self):
        return self.core_obj.check_upload_status()
