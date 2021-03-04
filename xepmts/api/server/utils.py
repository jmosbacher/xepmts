from werkzeug.wsgi import pop_path_info, peek_path_info

class PathDispatcher:

    def __init__(self, base_app, app_dict):
        self.base_app = base_app
        self.apps = app_dict

    def __call__(self, environ, start_response):
        app = self.apps.get(peek_path_info(environ), self.base_app)
        return app(environ, start_response)
