import datetime
import functools
import hashlib
import string
import time
import zlib

from tornado.web import HTTPError, RequestHandler
from peewee import IntegrityError

from models import User, Token, Repo, HMap, CSet, Blob

def authenticated(method):
    """Decorate API methods to require user authentication via token."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            raise HTTPError(401)
        return method(self, *args, **kwargs)
    return wrapper

def shasum(s):
    return hashlib.sha1(s).digest()

# This factor determines whether a snapshot is stored rather than a delta,
# depending on the accumulated size of the latest snapshot and subsequent
# deltas. I.e. for the latest snapshot `snap`, deltas `d1`, `d2`, ...,
# `dcur` and a new state `cur`, a new snapshot is stored if:
#
# `SNAPF * len(cur) <= len(snap) + len(d1) + len(d2) + ... + len(dcur)`
#
# So, larger values will result in longer delta chains and likely reduce
# storage size at the expense of higher revision reconstruction costs.
SNAPF = 1.0

# TODO: Tune zlib compression parameters `level`, `wbits`, `bufsize`?

def compress(s):
    return zlib.compress(s)

def decompress(s):
    return zlib.decompress(s)

class BaseHandler(RequestHandler):
    """Base class for all web API handlers."""

    def get_current_user(self):
        try:
            header = self.request.headers["Authorization"]
            method, value = header.split(" ")
            if method == "token":
                user = User.select().join(Token).where(Token.value == value)
                return user.get()
            else:
                return None
        except (KeyError, ValueError, User.DoesNotExist):
            return None

class RepoHandler(BaseHandler):
    """Processes repository calls: Push, timegate, memento, timemap etc."""

    # def head(self, username, reponame):
    #     pass

    def get(self, username, reponame):
        timemap = self.get_query_argument("timemap") == "true"
        index = self.get_query_argument("index") == "true"
        key = self.get_query_argument("key")

        if (index and timemap) or (index and key) or (timemap and not key):
            raise HTTPError(400)

        ts = float(self.get_query_argument("timestamp")) or time.time()

        try:
            repo = (Repo
                .select(Repo.id)
                .join(User)
                .where((User.name == username) & (Repo.name == reponame))
                .naive()
                .get())
        except Repo.DoesNotExist:
            raise HTTPError(404)

        if key and not timemap:
            # Recreate the resource for the given key in its latest state -
            # if no `timestamp` was provided - or in the state it was in at
            # the time indicated by the passed `timestamp` argument.

            sha = shasum(key)

            # Fetch all relevant changes from the last "non-delta" onwards,
            # ordered by time. The returned delta-chain consists of either:
            # a snapshot followed by 0 or more deltas, or
            # a single delete.
            chain = list(CSet
                .select(CSet.time, CSet.type)
                .where(
                    (CSet.repo == repo) &
                    (CSet.hkey == sha) &
                    (CSet.time <= ts) &
                    (CSet.time >= SQL(
                        "COALESCE((SELECT time FROM cset"
                        "WHERE repo_id = %s"
                        "AND hkey_id = %s"
                        "AND time <= %s"
                        "AND type != %s"
                        "ORDER BY time DESC"
                        "LIMIT 1), 0)",
                        repo.id, sha, ts, CSet.DELTA
                    )))
                .order_by(CSet.time)
                .naive())

            if len(chain) == 0:
                # A resource does not exist for the given key.
                raise HTTPError(404)

            if chain[0].type == CSet.DELETE:
                # The last change was a delete. Return a 404 response with
                # appropriate "Link" and "Memento-Datetime" headers.
                raise HTTPError(404) # TODO

            # Load the data required in order to restore the resource state.
            blobs = (Blob
                .select(Blob.data)
                .where(
                    (Blob.repo == repo) &
                    (Blob.hkey == sha) &
                    (Blob.time << map(lambda e: e.time, chain)))
                .order_by(Blob.time)
                .naive())

            quads = set()

            for i, blob in enumerate(blob.iterator()):
                data = decompress(blob.data)

                if i == 0:
                    quads.update(???(data))
                else:
                    upd(quads, data)
                    # quads.discard(deletion)
                    # quads.add(addition)

            self.write(???(quads))
        elif key and timemap:
            # Generate a timemap containing historic change information
            # for the requested key.

            sha = shasum(key)

            # TODO: Gen. timemap by selecting timestamps from csets for resource
            # TODO: Paginate?
        elif index:
            # Generate an index of all URIs contained in the dataset at the
            # provided point in time or in its current state.

            # TODO Paginate! Filter? (See peewee's `.paginate()`)

            # uris = (HMap
            #     .select(HMap.val)
            #     .join(CSet)
            #     .where(
            #         (CSet.repo == repo) &
            #         (CSet.)
            #     ))

            pass
        else:
            raise HTTPError(400)

    @authenticated
    def put(self, username, reponame):
        # Create a new revision of the resource specified by `key`.

        key = self.get_query_argument("key")

        if username != self.current_user.name:
            raise HTTPError(403)

        if not key:
            raise HTTPError(400)

        ts = float(self.get_query_argument("timestamp")) or time.time()

        try:
            repo = (Repo
                .select(Repo.id)
                .join(User)
                .where((User.name == username) & (Repo.name == reponame))
                .naive()
                .get())
        except Repo.DoesNotExist:
            raise HTTPError(404)

        sha = shasum(key)

        chain = list(CSet
            .select(CSet.time, CSet.type, CSet.len)
            .where(
                (CSet.repo == repo) &
                (CSet.hkey == sha) &
                (CSet.time >= SQL(
                    "COALESCE((SELECT time FROM cset"
                    "WHERE repo_id = %s"
                    "AND hkey_id = %s"
                    "AND type != %s"
                    "ORDER BY time DESC"
                    "LIMIT 1), 0)",
                    repo.id, sha, CSet.DELTA
                )))
            .order_by(CSet.time)
            .naive())

        if len(chain) > 0 and ts < chain[-1].time:
            # Appended timestamps must be monotonically increasing!
            raise HTTPError(400)

        if len(chain) == 0:
            # Mapping for `key` likely does not exist:
            # Store the SHA-to-KEY mapping in HMap,
            # looking out for possible collisions.
            try:
                HMap.create(sha=sha, val=key)
            except IntegrityError:
                val = HMap.select(HMap.val).where(sha=sha).scalar()
                if val != key:
                    raise HTTPError(500)

        # Parse and normalize (N-Quads)
        cur = ???(???(self.request.body))

        acclen = reduce(lambda s, e: s + e.len, chain, 0)
        snapc = compress(cur)

        if (len(chain) == 0 or
            chain[0].type == CSet.DELETE or
            SNAPF * len(snapc) <= acclen):
            # Store a snapshot of the current state
            pass
        else:
            # Store a directed delta between the previous and current state
            pass

    @authenticated
    def delete(self, username, reponame):
        # Check whether the key exists and if maybe the last change already is
        # a delete, else insert a `CSet.DELETE` entry without any blob data.

        key = self.get_query_argument("key")

        if username != self.current_user.name:
            raise HTTPError(403)

        if not key:
            raise HTTPError(400)

        ts = float(self.get_query_argument("timestamp")) or time.time()

        try:
            repo = (Repo
                .select(Repo.id)
                .join(User)
                .where((User.name == username) & (Repo.name == reponame))
                .naive()
                .get())
        except Repo.DoesNotExist:
            raise HTTPError(404)

        sha = shasum(key)

        last = CSet.select(CSet.type)
