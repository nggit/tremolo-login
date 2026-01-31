#!/usr/bin/env python3

import multiprocessing as mp
import os
import signal
import sys
import unittest

# makes imports relative from the repo directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.http_server import (  # noqa: E402
    app,
    HTTP_HOST,
    HTTP_PORT,
    EXPIRED_ID,
    BADFILE_ID,
    get_sid
)
from tests.netizen import HTTPClient  # noqa: E402


class TestHTTP(unittest.TestCase):
    def setUp(self):
        print('\r\n[', self.id(), ']')

        self.client = HTTPClient(HTTP_HOST, HTTP_PORT, timeout=10, retries=10)

    def test_get_ok(self):
        with self.client:
            response = self.client.send(
                b'GET /login HTTP/1.1',
                b'User-Agent: UA'
            )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'None')
            self.assertEqual(
                response.headers[b'cache-control'][0][:9], b'no-cache,'
            )
            self.assertEqual(response.headers[b'set-cookie'][0][:5], b'sess=')

            response = self.client.send(
                b'GET /login HTTP/1.0',
                b'User-Agent: UA'
            )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'OK')

    def test_get_ok_auth_bearer(self):
        with self.client:
            response = self.client.send(
                b'GET /login HTTP/1.1',
                b'User-Agent: UA'
            )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'None')

            session_id = response.headers[b'set-cookie'][0][5:69]
            token = session_id + get_sid(session_id).encode('latin-1')

            response = self.client.send(
                b'GET /login HTTP/1.0',
                b'Authorization: Bearer  %s ' % token
            )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'OK')

    def test_get_missing_bearer_prefix(self):
        with self.client:
            response = self.client.send(
                b'GET /login HTTP/1.0',
                b'Authorization: Basic token'
            )

            self.assertEqual(response.status, 400)
            self.assertEqual(response.message, b'Bad Request')
            self.assertEqual(response.body(), b'missing Bearer prefix')

    def test_get_ok_no_setcookie(self):
        with self.client:
            response = self.client.send(b'GET /about HTTP/1.1')

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'None')
            self.assertFalse(b'cache-control' in response.headers)
            self.assertFalse(b'set-cookie' in response.headers)

    def test_get_notfound(self):
        with self.client:
            response = self.client.send(b'GET /invalid HTTP/1.1')

            self.assertEqual(response.status, 404)
            self.assertEqual(response.message, b'Not Found')
            self.assertFalse(b'set-cookie' in response.headers)

    def test_get_expired_sess(self):
        with self.client:
            response = self.client.send(
                b'GET /login HTTP/1.1',
                b'User-Agent: UA',
                b'Cookie: sess=%s' % EXPIRED_ID.encode('latin-1')
            )

            self.assertEqual(response.status, 403)
            self.assertEqual(response.message, b'Forbidden')
            self.assertEqual(response.body(), b'Forbidden')

        with self.client:
            response = self.client.send(
                b'GET /login HTTP/1.1',
                b'User-Agent: UA',
                b'Cookie: sess=%s' % BADFILE_ID.encode('latin-1')
            )

            self.assertEqual(response.status, 403)
            self.assertEqual(response.message, b'Forbidden')
            self.assertEqual(response.body(), b'Forbidden')

    def test_get_invalid_sess_cookie(self):
        with self.client:
            response = self.client.send(
                b'GET /login HTTP/1.1',
                b'User-Agent: UA',
                b'Cookie: sess=/../etc/passwd'
            )

            self.assertEqual(response.status, 403)
            self.assertEqual(response.message, b'Forbidden')
            self.assertEqual(response.body(), b'invalid token')


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
