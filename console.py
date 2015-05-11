#!/usr/bin/env python

# Load application environment and initialize models

from database import MariaDB as Database

from config import settings, dbconf, bsconf
from models import *

import models

database = Database(**dbconf)
blobstore = None # Blobstore(bsconf.nodes, **bsconf.opts)
models.initialize(database, blobstore)

# Drop into IPython

from IPython import embed
from IPython import Config

config = Config()

prompt = config.PromptManager
prompt.in_template = ">>> "
prompt.in2_template = "... "
prompt.out_template = ""
prompt.justify = False

ishell = config.InteractiveShell
ishell.confirm_exit = False

mode = ("debug" if settings["debug"] else "default")
banner = "Loaded %s environment\nType %%quickref for help" % mode

del prompt, ishell # clean up namespace

embed(config=config, banner1=banner)
