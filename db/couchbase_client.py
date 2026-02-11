from __future__ import annotations

from datetime import timedelta

from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.exceptions import CouchbaseException

from config.app_cfg import (
    CB_CONNSTR, CB_USERNAME, CB_PASSWORD,
    CB_BUCKET, CB_SCOPE, CB_COLLECTION
)


class CouchbaseRepo:
    def __init__(self):
        self.cluster: Cluster | None = None
        self.bucket = None
        self.scope = None
        self.collection = None

    def connect(self):
        if not CB_PASSWORD:
            raise RuntimeError("CB_PASSWORD is empty. Set it in .env or export CB_PASSWORD.")

        auth = PasswordAuthenticator(CB_USERNAME, CB_PASSWORD)
        self.cluster = Cluster(CB_CONNSTR, ClusterOptions(auth))

        self.cluster.wait_until_ready(timedelta(seconds=60))

        self.bucket = self.cluster.bucket(CB_BUCKET)
        try:
            self.bucket.wait_until_ready(timedelta(seconds=60))
        except Exception:
            pass

        self.scope = self.bucket.scope(CB_SCOPE)
        self.collection = self.scope.collection(CB_COLLECTION)

        self._ensure_primary_index()

    def _ensure_primary_index(self):
        stmt = f"CREATE PRIMARY INDEX IF NOT EXISTS ON `{CB_BUCKET}`.`{CB_SCOPE}`.`{CB_COLLECTION}`"
        try:
            self.cluster.query(stmt).execute()
        except CouchbaseException:
            pass

    def upsert(self, key: str, doc: dict):
        return self.collection.upsert(key, doc)

    def get(self, key: str) -> dict:
        return self.collection.get(key).content_as[dict]

    def query(self, statement: str, parameters: dict | None = None) -> list[dict]:
        if parameters is None:
            parameters = {}
        res = self.cluster.query(statement, QueryOptions(named_parameters=parameters))
        return [row for row in res]


repo = CouchbaseRepo()