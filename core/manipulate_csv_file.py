import logging
import os
import random
import string

import pandas as pd

from config_master import DEFAULT_DOMAIN
from email_verifer.settings import BASE_DIR, MEDIA_ROOT

log = logging.getLogger(__name__)


class CSVJSON:
    def __init__(self, csv_file_location):
        self.csv_file_location = os.path.join(BASE_DIR, csv_file_location)
        self.excel_dict_conversion_list = None
        self.json_file_location = os.path.join(MEDIA_ROOT, self.randomword(20) + '.json')
        self.new_dict_list = None

    def randomword(self, length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def convert_csv_to_json(self):
        if self.csv_file_location.split('.')[-1] == 'csv':
            df_json = pd.read_csv(self.csv_file_location)
        else:
            df_json = pd.read_excel(self.csv_file_location)
        self.excel_dict_conversion_list = df_json.to_dict('records')
        return self.excel_dict_conversion_list

    def convert_dict_to_csv(self, dict_list):
        df = pd.DataFrame(dict_list)
        name = os.path.join(MEDIA_ROOT, self.randomword(32) + '.csv')
        df.to_csv(name)
        return name

    def convert_excel_dict_list_to_json_format(self):
        if self.excel_dict_conversion_list:
            new_dict_list = []
            dict_headers = self.excel_dict_conversion_list[0].keys()
            for dict_item in self.excel_dict_conversion_list:
                new_dict = {}
                for header in dict_headers:
                    if str(dict_item.get(header)) == 'nan':
                        dict_value = None
                    else:
                        dict_value = dict_item.get(header)
                    new_dict[header.lower().replace(' ', '_')] = dict_value
                new_dict_list.append(new_dict)
                self.new_dict_list = new_dict_list
            return self.new_dict_list

    def to_json(self):
        self.convert_csv_to_json()
        return self.convert_excel_dict_list_to_json_format()

    def add_email_from_name_combinations(self, ):
        new_email_list = []
        for item in self.new_dict_list:
            if item.get('first_name'):
                first_name = item.get('first_name').lower()
            else:
                first_name = item.get('first_name')
            if item.get('last_name'):
                last_name = item.get('last_name').lower()
            else:
                last_name = item.get('last_name')
            if item.get('domain'):
                domain = item.get('domain').lower()
            else:
                domain = DEFAULT_DOMAIN
            new_email_list.append({'email': f'{str(first_name)}@{str(domain)}'})
            new_email_list.append({'email': f'{str(first_name)}.{str(last_name)}@{str(domain)}'})
            new_email_list.append({'email': f'{str(first_name)[0]}.{str(last_name)}@{str(domain)}'})
            new_email_list.append({'email': f'{str(first_name)}.{str(last_name)[0]}@{str(domain)}'})
            new_email_list.append({'email': f'{str(first_name)}_{str(last_name)}@{str(domain)}'})
            new_email_list.append({'email': f'{str(first_name)}-{str(last_name)}@{str(domain)}'})
        self.new_dict_list = new_email_list
        return self.new_dict_list
