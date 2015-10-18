sentry-ssdb-nodestorage
=====================

[Sentry](https://github.com/getsentry/sentry) extension implementing the
NodeStorage interface for [SSDB](http://ssdb.io)

# Installation

First install libmsgpack including headers, on Ubuntu this would be:

```bash
$ apt-get install libmsgpack-dev
```

Then install the python package from github (inside the sentry virtualenv):
```bash
$ source bin/active
$ pip install git+https://github.com/felixbuenemann/sentry-ssdb-nodestore
```

# Configuration

Add this to your `sentry.conf.py`:

```python
SENTRY_NODESTORE = 'sentry_ssdb_nodestore.backend.SSDBNodeStorage'
SENTRY_NODESTORE_OPTIONS = {
    'host': 'localhost',
    'port': 8888,
    # Never auto-expire keys (default)
    'ttl': None,
    # Expire keys after one month (specify in seconds)
    # 'ttl': 60*60*24*30,
    # Delete this many keys at once during manual cleanup,
    # this does not limit the amount of keys deleted!
    'batchsize:': 1000,
}
```

# Why should you use it?

The SSDB storage has a similar storage efficiency as the built-in Riak
nodestore, but is much easier to setup and has lower system requirements.

# Why should you not use it?

Because it has not yet been used extensively in production and does not
yet have any test coverage. It has only been tested with Sentry 7.7.x.

SSDB allows for Master-Slave or Master-Master replication, but the used
ssdb.py client does not currently support host failover, so you'd have
to put a load balancer like haproxy in front of your nodes. You also
duplicate data across nodes, while Riak stores only enough copies of data
to be able to recover from node failures.

# Features

* Auto Expire keys after a specified duration (optional)
* Manual Expire through scan + batch delete (keys contain timestamps)
* Efficient and fast (de)serialization using MessagePack
* Binary keys and values to save space/improve compression
* Compression handled by the SSDB LevelDB backend

# Differences to existing backends

The default django database nodestore serializes the data using
pickle's slow and inefficient text based protocol, then compresses
the serialized data using gzip, encodes both key and zipped data
using Base64 and stores it into the nodestore\_node database table.

The SSDB nodestore uses binary storage for both keys and values,
avoiding the data bloat caused by base64 encoding. In addition
keys are prefixed by a 64-Bit unix timestamp, to allow manual
cleanup of keys based on their age, which is not possible with
most non-SQL nodestores.

Data is not compressed before storage into SSDB, because it uses
Google's LevelDB as backend, which features compression of the
whole database using the Snappy compression algorithmn.

Whole database compression is much more efficient than compressing
single values, because it can compress similar content in multiple
keys. For example multiple occurences of the same exception will
have very similar backtraces and even different exceptions from the
same app will have very similar environment and installed packages.

Note that the SSDB server configuration defines thresholds after which
database compaction is triggered, so you LevelDB database might grow to
to a gigabyte and then suddenly shrink to just a couple megabytes.
You can tune this in `ssdb.conf` using the `leveldb.compaction_speed` key.
Lower values might reduce write throughput, but unless you have a very
high number of exceptions that will probably not be an issue.

# Alternatives

Sentry comes with several built-in nodestore backends:

* DjangoNodeStorage: The default, stores to main SQL database.
* RiakNodeStorage: For very large deployments with multiple storage nodes.
* CassandraNodeStorage: Similar use cases as the Riak store.

And third party nodestore backends:

* [S3NodeStorage](https://github.com/ewdurbin/sentry-s3-nodestore): Let Amazon worry about storage and HA.

If you know other NodeStorage implementations, please submit a pull request
to list them here.
