import requests
import json


class Resource:

    def __init__(self, id):
        self.id = id

    def get_everything(self):
        response = requests.get('http://localhost:5000/api/3/action/resource_show?id=' + self.id)
        response_dict = json.loads(response.text)
        assert response_dict['success'] is True
        return response_dict['result']
