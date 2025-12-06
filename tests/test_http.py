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
from tests.netizen import HTTPClient  # noqa: E402

_EXPIRES = time.time() + 1800


class TestHTTP(unittest.TestCase):
    def setUp(self):
        print('\r\n[', self.id(), ']')

        self.client = HTTPClient(HTTP_HOST, HTTP_PORT, timeout=10, retries=10)

    def test_get_forbidden(self):
        with self.client:
            response = self.client.send(b'GET / HTTP/1.0')

            self.assertEqual(response.status, 403)
            self.assertEqual(response.message, b'Forbidden')
            self.assertEqual(response.body(), b'Forbidden')

    def test_get_ok(self):
        with self.client:
            response = self.client.send(
                b'GET / HTTP/1.0',
                b'User-Agent: UA',
                b'Cookie: sess=5e55.%d' % _EXPIRES
            )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'OK')


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
