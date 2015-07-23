from tornado.web import url

import handlers.web
import handlers.api

routes = [
    # Home routes
    url(r"/", handlers.web.HomeHandler, name="web:home"),
    url(r"/search", handlers.web.SearchHandler, name="web:search"),
    url(r"/join", handlers.web.JoinHandler, name="web:join"),

    # Auth routes
    url(r"/auth", handlers.web.AuthHandler, name="web:auth"),
    url(r"/auth/github", handlers.web.GitHubAuthHandler,
        name="web:github-auth"),
    url(r"/deauth", handlers.web.DeauthHandler, name="web:deauth"),

    # Account routes
    url(r"/create", handlers.web.CreateRepoHandler, name="web:create-repo"),
    url(r"/settings", handlers.web.SettingsHandler, name="web:settings"),
    url(r"/settings/account/edit", handlers.web.EditUserHandler,
        name="web:edit-user"),
    url(r"/settings/tokens/new", handlers.web.NewTokenHandler,
        name="web:new-token"),
    url(r"/settings/tokens/([0-9]+)/del", handlers.web.DelTokenHandler,
        name="web:del-token"),

    # User and repo routes
    url(r"/([^/]+)", handlers.web.UserHandler, name="web:user"),
    url(r"/([^/]+)/([^/]+)", handlers.web.RepoHandler, name="web:repo"),
    url(r"/([^/]+)/([^/]+)/([0-9]{14})/(.+)", handlers.web.MementoHandler,
        name="web:memento"),
    url(r"/([^/]+)/([^/]+)/history/(.+)", handlers.web.TimemapHandler,
        name="web:timemap"),

    # API routes
    url(r"/api/([^/]+)/([^/]+)/([0-9]{14})/(.+)", handlers.api.MementoHandler,
        name="api:memento"),
    url(r"/api/([^/]+)/([^/]+)/([0-9]{14})", handlers.api.IndexMementoHandler,
        name="api:index-memento"),
    url(r"/api/([^/]+)/([^/]+)/history/(.+)", handlers.api.TimemapHandler,
        name="api:timemap"),
    url(r"/api/([^/]+)/([^/]+)/(.+)", handlers.api.ResourceHandler,
        name="api:resource"),
    url(r"/api/([^/]+)/([^/]+)", handlers.api.IndexHandler,
        name="api:index"),

    # Aux routes
    url(r".*", handlers.web.ErrorHandler, dict(status_code=404)), # catch all
]

# GET   /                                 Homepage
# GET   /search                           Search users and repositories
# GET   /join                             Provide account info for a new user
# POST  /join                             Create a new user account
# GET   /auth                             Sign in form, provide credentials
# POST  /auth                             Sign in, create session
# GET   /auth/github                      Authenticate via GitHub OAuth
# POST  /deauth                           Sign out, destroy session
# GET   /create                           Enter information for new repository
# POST  /create                           Create new repository
# GET   /settings                         Settings overview page
# GET   /settings/account/edit            Edit user account settings
# POST  /settings/account/edit            Update user account settings
# GET   /settings/tokens/new              Provide information for new API token
# POST  /settings/tokens/new              Generate a new API token
# POST  /settings/tokens/:id/del          Delete API token
# GET   /:user                            User page
# GET   /:user/:repo                      Repository access
#
# PUT   /api/:user/:repo/:uri             Push API (opt. ?datetime=DATESTR)
# DELETE /api/:user/:repo/:uri
#
# GET   /api/:user/:repo/:datetime/:uri   Memento
# GET   /api/:user/:repo/history/:uri     TimeMap
# GET   /api/:user/:repo/:uri             TimeGate
# GET   /api/:user/:repo                  Index TimeGate (opt. ?page=INT)
# GET   /api/:user/:repo/:datetime        Index Memento (opt. ?page=INT)
