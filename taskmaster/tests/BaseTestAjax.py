from taskmaster.tests.BaseTest import BaseTest


class BaseTestAjax(BaseTest):

    def setUp(self, path='') -> None:
        super(BaseTestAjax, self).setUp(path)
        self.path = path

    def get(self, data=None):
        if data is None:
            data = {}
        return self.client.get(self.path, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def post(self, data=None):
        if data is None:
            data = {}
        return self.client.post(self.path, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
