from tornado.web import url

import handlers.web
import handlers.api

routes = [
    url(r"/", handlers.web.HomeHandler, name="web:home"),
    url(r"/search", handlers.web.SearchHandler, name="web:search"),
    url(r"/join", handlers.web.JoinHandler, name="web:join"),
    url(r"/auth", handlers.web.AuthHandler, name="web:auth"),
    url(r"/auth/github", handlers.web.GitHubAuthHandler,
        name="web:github-auth"),
    url(r"/deauth", handlers.web.DeauthHandler, name="web:deauth"),
    url(r"/create", handlers.web.CreateRepoHandler, name="web:create-repo"),
    url(r"/settings", handlers.web.SettingsHandler, name="web:settings"),
    url(r"/settings/account/edit", handlers.web.EditUserHandler,
        name="web:edit-user"),
    url(r"/settings/tokens/new", handlers.web.NewTokenHandler,
        name="web:new-token"),
    url(r"/settings/tokens/([0-9]+)/del", handlers.web.DelTokenHandler,
        name="web:del-token"),
    url(r"/([^/]+)", handlers.web.UserHandler, name="web:user"),
    url(r"/([^/]+)/([^/]+)", handlers.web.RepoHandler, name="web:repo"),
    url(r"/api/([^/]+)/([^/]+)", handlers.api.RepoHandler, name="api:repo"),
    url(r".*", handlers.web.ErrorHandler, dict(status_code=404)), # catch all
]

# GET   /                               Homepage
# GET   /search                         Search users and repositories
# GET   /join                           Provide account info for a new user
# POST  /join                           Create a new user account
# GET   /auth                           Sign in form, provide credentials
# POST  /auth                           Sign in, create session
# GET   /auth/github                    Authenticate via GitHub OAuth
# POST  /deauth                         Sign out, destroy session
# GET   /create                         Enter information for new repository
# POST  /create                         Create new repository
# GET   /settings                       Settings overview page
# GET   /settings/account/edit          Edit user account settings
# POST  /settings/account/edit          Update user account settings
# GET   /settings/tokens/new            Provide information for a new API token
# POST  /settings/tokens/new            Generate a new API token
# POST  /settings/tokens/:id/del        Delete API token
# GET   /:user                          User page
# GET   /:user/:repo                    Repository access
#
# PUT   /api/:user/:repo?key=URI
# PUT   /api/:user/:repo?key=URI&datetime=DATETIME
#
# GET   /api/:user/:repo?key=URI
# GET   /api/:user/:repo?key=URI&datetime=DATETIME
# GET   /api/:user/:repo?key=URI&timemap=true
# GET   /api/:user/:repo?index=true&page=1
