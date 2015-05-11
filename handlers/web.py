import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    """Base class for all web front end handlers."""

    def get_current_user(self):
        uid = self.get_secure_cookie("uid")
        user = User.get(User.id == uid) if uid else None
        return user

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render("error/404.html")
        else:
            self.render("error/gen.html")

class HomeHandler(BaseHandler):
    """Renders the website index page - nothing more."""

    def get(self):
        self.render("home/index.html")

class ErrorHandler(BaseHandler):
    """Generates an error response with ``status_code`` for all requests."""

    def initialize(self, status_code):
        self.set_status(status_code)

    def prepare(self):
        raise tornado.web.HTTPError(self.get_status())

    def check_xsrf_cookie(self):
        pass
