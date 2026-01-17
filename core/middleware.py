class HistoryMiddleware:
    def __init__(self, handler):
        self.handler = handler
        self.debugUrl = [
            '/__debug__/render_panel/',
            '/__reload__/events/'
        ]

    def __call__(self, request):
        if 'history' not in request.session:
            request.session['history'] = []

        if request.method == 'GET':
            path = request.path
            if not request.session['history'] or request.session['history'][-1] != path and path not in self.debugUrl:
                request.session['history'].append(path)
                request.session['history'] = request.session['history'][-20:]
                request.session.modified = True

        return self.handler(request)
