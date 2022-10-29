from taskmaster.tests.BaseTest import BaseTest


class BaseTestViews(BaseTest):

    def setUp(self, path='') -> None:
        super(BaseTestViews, self).setUp(path)
        self.path = path

    def get(self, data=None, path=None):
        data = data or {}
        path = path or self.path
        return self.client.get(path, data)

    def post(self, data=None, path=None):
        data = data or {}
        path = path or self.path
        return self.client.post(path, data, follow=True)
