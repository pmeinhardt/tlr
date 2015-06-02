import functools
import random

import tornado.auth
import tornado.escape
import tornado.gen
import tornado.httpclient
import tornado.web

from tornado.web import HTTPError, RequestHandler
from tornado.web import authenticated

from models import User, Repo, Token

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
            users = User.select().where(User.name ** pattern)
        else:
            repos = []
            users = []

        self.render("search/show.html", query=query, repos=repos, users=users)

class UserHandler(BaseHandler):
    def get(self, username):
        try:
            user = User.select().where(User.name == username).get()
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
    @authenticated
    def get(self):
        tokens = self.current_user.tokens
        title = "Account settings"
        self.render("settings/index.html", title=title, tokens=tokens)

    def on_finish(self):
        q = Token.update(seen=True).where(Token.user == self.current_user)
        q.execute()

class NewTokenHandler(BaseHandler):
    @authenticated
    def get(self):
        self.render("tokens/new.html")

    @authenticated
    def post(self):
        user = self.current_user
        desc = self.get_argument("description")
        value = "%040x" % random.randrange(16**40)
        # TODO: Retry on duplicate token value (peewee.IntegrityError)?
        Token.create(user=user, value=value, desc=desc)
        self.redirect(self.reverse_url("web:settings"))

class DelTokenHandler(BaseHandler):
    @authenticated
    def post(self, id):
        try:
            token = Token.get((Token.user == self.current_user) & (Token.id == id))
            token.delete_instance()
            self.redirect(self.reverse_url("web:settings"))
        except:
            raise HTTPError(404)

class GitHubOAuth2Mixin(tornado.auth.OAuth2Mixin):
    """GitHub authentication using OAuth2."""

    _OAUTH_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
    _OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    _OAUTH_SETTINGS_KEY = "github_oauth"

    @tornado.auth._auth_return_future
    def get_authenticated_user(self, redirect_uri, code, callback):
        http = self.get_auth_http_client()

        body = tornado.auth.urllib_parse.urlencode({
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": self.settings[self._OAUTH_SETTINGS_KEY]["key"],
            "client_secret": self.settings[self._OAUTH_SETTINGS_KEY]["secret"],
            "grant_type": "authorization_code",
        })

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        http.fetch(self._OAUTH_ACCESS_TOKEN_URL,
            functools.partial(self._on_access_token, callback),
            method="POST", headers=headers, body=body)

    def _on_access_token(self, future, response):
        if response.error:
            msg = "GitHub auth error: %s" % str(response)
            future.set_exception(tornado.auth.AuthError(msg))
            return

        args = tornado.escape.json_decode(response.body)
        future.set_result(args)

    def get_auth_http_client(self):
        return tornado.httpclient.AsyncHTTPClient()

class AuthHandler(BaseHandler, GitHubOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("code", False):
            user = yield self.get_authenticated_user(
                redirect_uri="http://localhost:5000/auth",
                code=self.get_argument("code"))
            self.write(user)
            # self.set_secure_cookie("uid", str(user.id))
            # self.redirect(self.get_argument("next", "/"))
        else:
            yield self.authorize_redirect(
                redirect_uri="http://localhost:5000/auth",
                client_id=self.settings["github_oauth"]["key"],
                response_type="code",
                scope=["user:email"])

    # def get(self):
    #     if not self.current_user:
    #         self.render("auth/new.html", title="Sign in - tailr")
    #     else:
    #         self.redirect("/")
    #
    # def post(self):
    #     user = User.get(User.name == self.get_argument("username"))
    #     self.set_secure_cookie("uid", str(user.id))
    #     self.redirect(self.get_argument("next", "/"))

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
