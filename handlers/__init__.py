import tornado.web

class RequestHandler(tornado.web.RequestHandler):
    """Base class for all request handlers."""

    def prepare(self):
        self.database.connect()
        return super(RequestHandler, self).prepare()

    def on_finish(self):
        if not self.database.is_closed():
            self.database.close()
        return super(RequestHandler, self).on_finish()

    @property
    def database(self):
        return self.application.database
