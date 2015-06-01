import datetime
import functools
import hashlib
import string
import time
import zlib

from tornado.web import HTTPError, RequestHandler
from tornado.escape import url_escape
from peewee import IntegrityError, SQL
import RDF

from models import User, Token, Repo, HMap, CSet, Blob

def authenticated(method):
    """Decorate API methods to require user authentication via token."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            raise HTTPError(401)
        return method(self, *args, **kwargs)
    return wrapper

# Query string date format, e.g. `...?datetime=2015-05-11-16:56:21`
QSDATEFMT = "%Y-%m-%d-%H:%M:%S"

# RFC 1123 date format, e.g. `Mon, 11 May 2015 16:56:21 GMT`
RFC1123DATEFMT = "%a, %d %b %Y %H:%M:%S GMT"

def date(s, fmt):
    return datetime.datetime.strptime(s, fmt)

def now():
    return datetime.datetime.utcnow()

# This factor (among others) determines whether a snapshot is stored rather
# than a delta, depending on the size of the latest snapshot and subsequent
# deltas. For the latest snapshot `base` and deltas `d1`, `d2`, ..., `dn`
# a new snapshot is definitely stored if:
#
# `SNAPF * len(base) <= len(d1) + len(d2) + ... + len(dn)`
#
# In short, larger values will result in longer delta chains and likely reduce
# storage size at the expense of higher revision reconstruction costs.
#
# TODO: Empirically determine a good value with real data/statistics.
SNAPF = 10.0

# TODO: Tune zlib compression parameters `level`, `wbits`, `bufsize`?

def compress(s):
    return zlib.compress(s)

def decompress(s):
    return zlib.decompress(s)

def shasum(s):
    return hashlib.sha1(s).digest()

def parse(s, fmt):
    stmts = set()
    parser = RDF.Parser(name="ntriples")
    for st in parser.parse_string_as_stream(s, "urn:x-default:tailr"):
        stmts.add(str(st) + " .")
    return stmts

def join(parts, sep):
    return string.joinfields(parts, sep)

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

    def check_xsrf_cookie(self):
        pass

class RepoHandler(BaseHandler):
    """Processes repository calls: Push, timegate, memento, timemap etc."""

    # def head(self, username, reponame):
    #     pass

    def get(self, username, reponame):
        timemap = self.get_query_argument("timemap", "false") == "true"
        index = self.get_query_argument("index", "false") == "true"
        key = self.get_query_argument("key", None)

        if (index and timemap) or (index and key) or (timemap and not key):
            raise HTTPError(400)

        datestr = self.get_query_argument("datetime", None)
        ts = datestr and date(datestr, QSDATEFMT) or now()

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
            # if no `datetime` was provided - or in the state it was in at
            # the time indicated by the passed `datetime` argument.

            self.set_header("Content-Type", "application/n-quads")
            # self.set_header("Vary", "accept-datetime")

            sha = shasum(key.encode("utf-8"))

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
                        "COALESCE((SELECT time FROM cset "
                        "WHERE repo_id = %s "
                        "AND hkey_id = %s "
                        "AND time <= %s "
                        "AND type != %s "
                        "ORDER BY time DESC "
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

            if len(chain) == 1:
                # Special case, where we can simply return
                # the blob data of the snapshot.
                snap = blobs.first().data
                return self.finish(decompress(snap))

            stmts = set()

            for i, blob in enumerate(blobs.iterator()):
                data = decompress(blob.data)

                if i == 0:
                    # Base snapshot for the delta chain
                    stmts.update(data.splitlines())
                else:
                    for line in data.splitlines():
                        mode, stmt = line[0], line[2:]
                        if mode == "A":
                            stmts.add(stmt)
                        else:
                            stmts.discard(stmt)

            self.write(join(stmts, "\n"))
        elif key and timemap:
            # Generate a timemap containing historic change information
            # for the requested key.

            sha = shasum(key.encode("utf-8"))

            csets = (CSet
                .select(CSet.time)
                .where((CSet.repo == repo) & (CSet.hkey == sha))
                .order_by(CSet.time.desc())
                .naive())

            # Serialize into Link format
            # TODO: Paginate?

            csit = csets.iterator()

            try:
                first = csit.next()
            except StopIteration:
                # Resource for given key does not exist.
                raise HTTPError(404)

            req = self.request
            base = req.protocol + "://" + req.host + req.path

            m = (',\n<' + base + '?key=' + url_escape(key) + '&datetime={0}>'
                '; rel="memento"'
                '; datetime="{1}"'
                '; type="application/n-quads"')

            self.set_header("Content-Type", "application/link-format")
            self.write('<' + key + '>; rel="original"')
            self.write(m.format(first.time.strftime(QSDATEFMT),
                first.time.strftime(RFC1123DATEFMT)))

            for cs in csit:
                self.write(m.format(cs.time.strftime(QSDATEFMT),
                    cs.time.strftime(RFC1123DATEFMT)))
        elif index:
            # Generate an index of all URIs contained in the dataset at the
            # provided point in time or in its current state.

            # self.set_header("Vary", "accept-datetime")

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

        fmt = self.request.headers["Content-Type"]
        key = self.get_query_argument("key", None)

        if username != self.current_user.name:
            raise HTTPError(403)

        if not key:
            raise HTTPError(400)

        datestr = self.get_query_argument("datetime", None)
        ts = datestr and date(datestr, QSDATEFMT) or now()

        try:
            repo = (Repo
                .select(Repo.id)
                .join(User)
                .where((User.name == username) & (Repo.name == reponame))
                .naive()
                .get())
        except Repo.DoesNotExist:
            raise HTTPError(404)

        sha = shasum(key.encode("utf-8"))

        chain = list(CSet
            .select(CSet.time, CSet.type, CSet.len)
            .where(
                (CSet.repo == repo) &
                (CSet.hkey == sha) &
                (CSet.time >= SQL(
                    "COALESCE((SELECT time FROM cset "
                    "WHERE repo_id = %s "
                    "AND hkey_id = %s "
                    "AND type != %s "
                    "ORDER BY time DESC "
                    "LIMIT 1), 0)",
                    repo.id, sha, CSet.DELTA
                )))
            .order_by(CSet.time)
            .naive())

        if len(chain) > 0 and not ts > chain[-1].time:
            # Appended timestamps must be monotonically increasing!
            raise HTTPError(400)

        if len(chain) == 0:
            # Mapping for `key` likely does not exist:
            # Store the SHA-to-KEY mapping in HMap,
            # looking out for possible collisions.
            try:
                HMap.create(sha=sha, val=key)
            except IntegrityError:
                val = HMap.select(HMap.val).where(HMap.sha == sha).scalar()
                if val != key:
                    raise HTTPError(500)

        # Parse and normalize into a set of N-Quad lines
        stmts = parse(self.request.body, fmt)
        snapc = compress(join(stmts, "\n"))

        if len(chain) == 0 or chain[0].type == CSet.DELETE:
            # Provide dummy value for `patch` which is never stored.
            # If we get here, we always store a snapshot later on!
            patch = ""
        else:
            # Reconstruct the previous state of the resource
            prev = set()

            blobs = (Blob
                .select(Blob.data)
                .where(
                    (Blob.repo == repo) &
                    (Blob.hkey == sha) &
                    (Blob.time << map(lambda e: e.time, chain)))
                .order_by(Blob.time)
                .naive())

            for i, blob in enumerate(blobs.iterator()):
                data = decompress(blob.data)

                if i == 0:
                    # Base snapshot for the delta chain
                    prev.update(data.splitlines())
                else:
                    for line in data.splitlines():
                        mode, stmt = line[0], line[2:]
                        if mode == "A":
                            prev.add(stmt)
                        else:
                            prev.discard(stmt)

            # TODO: Check stmts != prev (actual change or bail out)

            patch = compress(join(
                map(lambda s: "D " + s, prev - stmts) +
                map(lambda s: "A " + s, stmts - prev), "\n"))

        # Calculate the accumulated size of the delta chain including
        # the (potential) patch from the previous to the pushed state.
        acclen = reduce(lambda s, e: s + e.len, chain[1:], 0) + len(patch)

        blen = len(chain) > 0 and chain[0].len or 0 # base length

        if (len(chain) == 0 or chain[0].type == CSet.DELETE or
            len(snapc) <= len(patch) or SNAPF * blen <= acclen):
            # Store the current state as a new snapshot
            Blob.create(repo=repo, hkey=sha, time=ts, data=snapc)
            CSet.create(repo=repo, hkey=sha, time=ts, type=CSet.SNAPSHOT,
                len=len(snapc))
        else:
            # Store a directed delta between the previous and current state
            Blob.create(repo=repo, hkey=sha, time=ts, data=patch)
            CSet.create(repo=repo, hkey=sha, time=ts, type=CSet.DELTA,
                len=len(patch))

    @authenticated
    def delete(self, username, reponame):
        # Check whether the key exists and if maybe the last change already is
        # a delete, else insert a `CSet.DELETE` entry without any blob data.

        key = self.get_query_argument("key")

        if username != self.current_user.name:
            raise HTTPError(403)

        if not key:
            raise HTTPError(400)

        datestr = self.get_query_argument("datetime", None)
        ts = datestr and date(datestr, QSDATEFMT) or now()

        try:
            repo = (Repo
                .select(Repo.id)
                .join(User)
                .where((User.name == username) & (Repo.name == reponame))
                .naive()
                .get())
        except Repo.DoesNotExist:
            raise HTTPError(404)

        sha = shasum(key.encode("utf-8"))

        try:
            last = (CSet
                .select(CSet.time, CSet.type)
                .where((CSet.repo == repo) & (CSet.hkey == sha))
                .order_by(CSet.time.desc())
                .limit(1)
                .naive()
                .get())
        except CSet.DoesNotExist:
            # No changeset was found for the given key -
            # the resource does not exist.
            raise HTTPError(400)

        if not ts > last.time:
            # Appended timestamps must be monotonically increasing!
            raise HTTPError(400)

        if last.type == CSet.DELETE:
            # The resource was deleted already, return instantly.
            return self.finish()

        # Insert the new "delete" change.
        CSet.create(repo=repo, hkey=sha, time=ts, type=CSet.DELETE, len=0)
