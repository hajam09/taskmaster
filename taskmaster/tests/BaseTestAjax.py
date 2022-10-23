from taskmaster.tests.BaseTest import BaseTest


class BaseTestAjax(BaseTest):

    def setUp(self, path='') -> None:
        super(BaseTestAjax, self).setUp(path)
        self.path = path

    def get(self, data=None):
        if data is None:
            data = {}
        return self.client.get(self.path, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def post(self, data=None, path=None):
        if data is None:
            data = {}

        if path is None:
            path = self.path
        return self.client.post(path, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def put(self, data=None, path=None):
        if data is None:
            data = {}

        if path is None:
            path = self.path
        return self.client.put(path, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest', follow=True)

    def delete(self, data=None, path=None):
        if data is None:
            data = {}

        if path is None:
            path = self.path
        return self.client.delete(path, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest', follow=True)
