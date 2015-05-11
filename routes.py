from tornado.web import url

import handlers.web
import handlers.api

routes = [
    url(r"/", handlers.web.HomeHandler, name="web:home"),
    # url(r"/search", handlers.web.SearchHandler, name="web:search"),
    # url(r"/join", handlers.web.JoinHandler, name="web:join"),
    # url(r"/auth", handlers.web.AuthHandler, name="web:auth"),
    # url(r"/deauth", handlers.web.DeauthHandler, name="web:deauth"),
    # url(r"/new", handlers.web.NewRepoHandler, name="web:new-repo"),
    # url(r"/settings", handlers.web.SettingsHandler, name="web:settings"),
    # url(r"/settings/tokens/new", NewTokenHandler, name="new-token"),
    # url(r"/settings/tokens/([0-9]+)/del", DelTokenHandler, name="del-token"),
    # url(r"/([^/]+)", handlers.web.UserHandler, name="web:user"),
    # url(r"/([^/]+)/([^/]+)", handlers.web.RepoHandler, name="web:repo"),
    url(r"/api/([^/]+)/([^/]+)", handlers.api.RepoHandler, name="api:repo"),
    url(r".*", handlers.web.ErrorHandler, dict(status_code=404)), # catch all
]

# GET   /                               Homepage
# GET   /search                         Search users and repositories
# GET   /join                           Provide account info for a new user
# POST  /join                           Create a new user account
# GET   /auth                           Sign in form, provide credentials
# POST  /auth                           Sign in, create session
# POST  /deauth                         Sign out, destroy session
# GET   /new                            Enter information for new repository
# POST  /new                            Create new repository
# GET   /settings                       Account settings (tokens etc.)
# GET   /settings/tokens/new            Provide information for a new API token
# POST  /settings/tokens/new            Generate a new API token
# POST  /settings/tokens/:id/del        Delete API token
# GET   /:user                          User page
# GET   /:user/:repo                    Repository access

# GET   /:user/:repo?index=true
# GET   /:user/:repo?key=URI
# GET   /:user/:repo?key=URI&datetime=TIMESTAMP
# GET   /:user/:repo?key=URI&timemap=true
