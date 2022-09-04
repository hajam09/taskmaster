from taskmaster.tests.BaseTest import BaseTest


class BaseTestViews(BaseTest):

    def setUp(self, path='') -> None:
        super(BaseTestViews, self).setUp(path)
        self.path = path

    def get(self, data=None):
        if data is None:
            data = {}
        return self.client.get(self.path, data)

    def post(self, data=None):
        if data is None:
            data = {}
        return self.client.post(self.path, data, follow=True)
