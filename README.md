sentry-ssdb-nodestorage
=====================

[Sentry](https://github.com/getsentry/sentry) extension implementing the
NodeStorage interface for [SSDB](http://ssdb.io)

# Installation

```bash
$ pip install sentry-ssdb-nodestore
```

# Configuration

```python
SENTRY_NODESTORE = 'sentry_ssdb_nodestore.backend.SSDBNodeStorage'
SENTRY_NODESTORE_OPTIONS = {
    'host': 'localhost',
    'port': 8888,
    # Never auto-expire keys (default)
    'ttl': None,
    # Expire keys after one month (specify in seconds)
    # 'ttl': 60*60*24*30,
    # Delete this many keys at once during manual cleanup
    'batchsize:': 1000,
}
```
