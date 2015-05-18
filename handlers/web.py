import tornado.escape
import tornado.web

from tornado.web import HTTPError, RequestHandler
from tornado.web import authenticated

from models import User, Repo

class BaseHandler(RequestHandler):
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

class SearchHandler(BaseHandler):
    def get(self):
        query = tornado.escape.url_unescape(self.get_argument("q", ""))

        if query:
            pattern = "%" + query + "%"
            repos = (Repo.select().join(User).alias("user")
                .where(Repo.name ** pattern))
        else:
            repos = []

        self.render("search/show.html", query=query, repos=repos)

class UserHandler(BaseHandler):
    def get(self, username):
        try:
            user = User.select().join(Repo).where(User.name == username).get()
            self.render("user/show.html", title=user.name, user=user)
        except User.DoesNotExist:
            raise HTTPError(404)

class RepoHandler(BaseHandler):
    def get(self, username, reponame):
        try:
            repo = (Repo.select().join(User).alias("user")
                .where((User.name == username) & (Repo.name == reponame))
                .get())
            title = repo.user.name + "/" + repo.name
            self.render("repo/show.html", title=title, repo=repo)
        except Repo.DoesNotExist:
            raise HTTPError(404)

class CreateRepoHandler(BaseHandler):
    @authenticated
    def get(self):
        user = self.current_user
        title = "Create a new repository"
        self.render("repo/new.html", title=title, user=user)

    @authenticated
    def post(self):
        reponame = self.get_argument("reponame", None)
        desc = self.get_argument("description", None)
        user = self.current_user
        if not reponame:
            self.redirect(self.reverse_url("web:create-repo"))
            return
        repo = Repo.create(user=user, name=reponame, desc=desc)
        self.redirect(self.reverse_url("web:repo", user.name, repo.name))

class SettingsHandler(BaseHandler):
    pass

class AuthHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("auth/new.html", title="Sign in - tailr")
        else:
            self.redirect("/")

    def post(self):
        user = User.get(User.name == self.get_argument("username"))
        self.set_secure_cookie("uid", str(user.id))
        self.redirect(self.get_argument("next", "/"))

class DeauthHandler(BaseHandler):
    def post(self):
        self.clear_cookie("uid")
        self.redirect("/")

class ErrorHandler(BaseHandler):
    """Generates an error response with ``status_code`` for all requests."""

    def initialize(self, status_code):
        self.set_status(status_code)

    def prepare(self):
        raise tornado.web.HTTPError(self.get_status())

    def check_xsrf_cookie(self):
        pass
