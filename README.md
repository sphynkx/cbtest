Test snippet for experiments with [CouchBase DB](https://www.couchbase.com/).

## Install DB
```bash
wget https://packages.couchbase.com/releases/7.6.1/couchbase-server-community-7.6.1-linux.x86_64.rpm
dnf -y install couchbase-server-community-7.6.1-linux.x86_64.rpm
```
Open http://localhost:8091 and create new bucket (e.g. `comments`), create admin user, set all other options.
You may also try to test request (in "Query"):
```sql
SELECT c.*
FROM `comments`.`_default`.`_default` c
WHERE c.type="comment" AND c.thread_id="thread::demo"
ORDER BY c.created_at;
```
Result will empty for now..


## Install app
__NOTE__: `couchbase` python module supports py-3.10 or lower.. Either need to build wheel manually.. So use `uv`..
```bash
dnf -y install uv
uv venv --python 3.10 .venv
cd cbtest
source .venv/bin/activate
uv pip install -r install/requirements.txt
```

Optionally set in `.env`:
```conf
CB_CONNSTR="couchbase://127.0.0.1"
CB_USERNAME="admin"
CB_PASSWORD="SECRET"
CB_BUCKET="comments"
```
Run:
```bash
uvicorn main:app --reload --port 8800
```
Check health: http://localhost:8800/api/health

Use: http://localhost:8800/ Add some branch of comments.. In DB console repeat Query (as above)..


## Queries
Full comments branch:
```sql
SELECT c.*
FROM `comments`.`_default`.`_default` c
WHERE c.type="comment" AND c.thread_id="thread::demo"
ORDER BY c.created_at;
```

Only root comments:
```sql
SELECT c.*
FROM `comments`.`_default`.`_default` AS c
WHERE c.type="comment"
  AND c.thread_id="thread::demo"
  AND (c.parent_id IS MISSING OR c.parent_id IS NULL OR c.parent_id = "")
ORDER BY c.created_at;
```

One level child replies on comment with <ID>:
```sql
SELECT c.*
FROM `comments`.`_default`.`_default` AS c
WHERE c.type="comment"
  AND c.thread_id="thread::demo"
  AND c.parent_id="comment::<ID>"
ORDER BY c.created_at;
```

Subbranch from comment with <ID>:
```sql
SELECT c.*
FROM `comments`.`_default`.`_default` AS c
WHERE c.type="comment"
  AND c.thread_id="thread::demo"
  AND ANY p IN c.path SATISFIES p="comment::<ID>" END
ORDER BY c.created_at;
```

Branch deepness:
```sql
SELECT MAX(c.depth) AS max_depth, COUNT(1) AS total
FROM `comments`.`_default`.`_default` AS c
WHERE c.type="comment" AND c.thread_id="thread::demo";
```


