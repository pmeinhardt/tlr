#!/usr/bin/env python

from database import MDB as Database

from config import dbconf, bsconf
from models import *

import models

if __name__ == "__main__":
    database = Database(**dbconf)
    blobstore = None # Blobstore(bsconf.nodes, **bsconf.opts)
    models.initialize(database, blobstore)
    database.create_tables([
        User,
        Token,
        Repo,
        HMap,
        CSet,
        Blob,
    ])
