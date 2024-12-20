#!/usr/bin/env python3

import multiprocessing as mp
import os
import signal
import sys
import time
import unittest

# makes imports relative from the repo directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.http_server import (  # noqa: E402
    app,
    HTTP_HOST,
    HTTP_PORT
)
from tests.utils import getcontents  # noqa: E402

_EXPIRES = time.time() + 1800


class TestHTTPServer(unittest.TestCase):
    def setUp(self):
        print('\r\n[', self.id(), ']')

    def test_get_forbidden(self):
        header, body = getcontents(host=HTTP_HOST,
                                   port=HTTP_PORT,
                                   method='GET',
                                   url='/',
                                   version='1.0')

        self.assertEqual(
            header[:header.find(b'\r\n')], b'HTTP/1.0 403 Forbidden'
        )

    def test_get_ok(self):
        header, body = getcontents(
            host=HTTP_HOST,
            port=HTTP_PORT,
            raw=b'GET / HTTP/1.0\r\nHost: localhost\r\n'
                b'User-Agent: UA\r\n'
                b'Cookie: sess=5e55.' + (b'%d' % _EXPIRES) +
                b'\r\n\r\n'
        )

        self.assertEqual(header[:header.find(b'\r\n')], b'HTTP/1.0 200 OK')
        self.assertEqual(b'OK', body)


if __name__ == '__main__':
    mp.set_start_method('spawn')

    p = mp.Process(
        target=app.run,
        kwargs=dict(host=HTTP_HOST, port=HTTP_PORT, debug=False)
    )
    p.start()

    try:
        unittest.main()
    finally:
        if p.is_alive():
            os.kill(p.pid, signal.SIGTERM)
            p.join()
