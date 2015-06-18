#!/usr/bin/env python

from database import PooledMDB as Database

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

define("port", default=5000, help="port to bind to", type=int)

from config import settings, dbconf, bsconf
from routes import routes

import models

class Application(tornado.web.Application):
    def __init__(self, dbconf, bsconf, handlers=None, **settings):
        super(Application, self).__init__(handlers, **settings)
        self.blobstore = None # Blobstore(bsconf.nodes, **bsconf.opts)
        self.database = Database(**dbconf)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = Application(dbconf, bsconf, routes, **settings)
    models.initialize(app.database, app.blobstore)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()
