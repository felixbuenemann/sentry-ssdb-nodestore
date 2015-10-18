"""
sentry_ssdb_nodestore.backend
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2015 by Felix Buenemann.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import msgpack
from ssdb import Client
#from pyssdb import Client
from collections import defaultdict
from operator import add
from six import iteritems
from base64 import b64decode, b64encode
from uuid import uuid4
from time import time, mktime
from struct import pack, unpack

from sentry.nodestore.base import NodeStorage

def dumps(data):
    return msgpack.dumps(data)

def loads(data):
    return data and msgpack.loads(data, encoding='utf-8')

def uids(base64_ids):
    return map(uid, base64_ids)

def uid(base64_id):
    return b64decode(base64_id)

def b64ids(uids):
    return map(b64id, uids)

def b64id(uid):
    return b64encode(uid)

# def datetime_to_uuid_v1_timestamp(timestamp):
#     posix_ts = mktime(timestamp.timetuple())
#     # Number of 100-ns intervals between
#     # Unix epoch 1970-01-01 00:00:00 and
#     # UUID epoch 1582-10-15 00:00:00
#     posix_uuid_v1_offset = 0x01b21dd213814000
#     uuid_ts = long(posix_ts * 1e7 + posix_uuid_v1_offset)
#     return uuid_ts

def tsbin(timestamp):
    # encode posix timestamp as 8 bytes with nanosecond precision
    # use big-endian to have proper sorting for scan/rscan
    return pack('>Q', int(timestamp*1e6))

def bints(binary):
    # decode timestamp part from node_id
    return unpack('>Q', binary[:8])[0]

class SSDBNodeStorage(NodeStorage):
    """
    A SSDB-based backend for storing node data.
    >>> SSDBNodeStorage(
    ...     host='localhost',
    ...     port=8888,
    ...     socket_timeout=2,
    ...     ttl=60*60*24*30,
    ...     batchsize=10000,
    ... )
    """

    def __init__(self, ttl=None, batchsize=1000, **kwargs):
        self.ttl = ttl
        self.batchsize = batchsize
        self.client = Client(**kwargs)

    def delete(self, id):
        """
        >>> nodestore.delete('key1')
        """
        self.client.delete(uid(id))

    def delete_multi(self, id_list):
        """
        Delete multiple nodes.

        >>> delete_multi(['key1', 'key2'])
        """
        self.client.multi_del(*uids(id_list))

    def get(self, id):
        """
        >>> data = nodestore.get('key1')
        >>> print data
        """
        return loads(self.client.get(uid(id)))

    def get_multi(self, id_list):
        """
        >>> data_map = nodestore.get_multi(['key1', 'key2')
        >>> print 'key1', data_map['key1']
        >>> print 'key2', data_map['key2']
        """
        # with self.client.pipeline() as pipe:
        #     for id in id_list: pipe.get(uid(id))
        #     values = pipe.execute()
        # return dict(zip(id_list, [loads(v) for v in values]))
        kv_list = self.client.multi_get(*uids(id_list))
        return defaultdict(lambda: None, map(lambda k, v: (b64id(k), loads(v)), *[iter(kv_list)]*2))

    def set(self, id, data):
        """
        >>> nodestore.set('key1', {'foo': 'bar'})
        """
        if self.ttl:
            self.client.setx(uid(id), dumps(data), self.ttl)
        else:
            self.client.set(uid(id), dumps(data))

    def set_multi(self, values):
        """
        >>> nodestore.set_multi({
        >>>     'key1': {'foo': 'bar'},
        >>>     'key2': {'foo': 'baz'},
        >>> })
        """
        # kv_list = [item for sublist in iteritems(values) for item in sublist]
        if self.ttl:
            # ssdb has no multi_setx, use piped setx instead
            with self.client.pipeline() as pipe:
                for id, data in iteritems(values):
                    pipe.setx(uid(id), dumps(data), self.ttl)
                pipe.execute()

            # TODO Benchmark against multi:set + expire loop
            # for id, data in iteritems(values):
            #     self.client.setx(uid(id), dumps(data), self.ttl)
        else:
            kv_list = reduce(lambda l, (k, v): add(l, (uid(k), dumps(v))), iteritems(values), ())
            self.client.multi_set(*kv_list)

    def generate_id(self):
        # ids are 32 byte base64, but stored as 24 byte binary
        return b64encode(tsbin(time()) + uuid4().bytes)

    def cleanup(self, cutoff_timestamp):
        # this is the smallest possible timestamp (1970-01-01)
        start  = tsbin(0)
        # mktime truncates milliseconds, add them back manually
        cutoff = tsbin(mktime(cutoff_timestamp.timetuple()) + cutoff_timestamp.microsecond/1e6)

        while True:
            keys = self.client.keys(start, cutoff, self.batchsize)
            count = len(keys)
            # print "Cleanup %016d -> %016d %d / %d" % (bints(start), bints(cutoff), count, self.batchsize)
            if count == 0: break
            self.client.multi_del(*keys)
            if count < self.batchsize: break
            start = keys[-1]

