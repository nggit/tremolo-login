#!/usr/bin/env python3

import hashlib
import hmac
import json
import os
import sys

from base64 import urlsafe_b64encode as b64encode

# makes imports relative from the repo directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tremolo import Application  # noqa: E402
from tremolo.exceptions import Forbidden  # noqa: E402
from tremolo_login import Session  # noqa: E402

HTTP_HOST = '127.0.0.1'
HTTP_PORT = 28000
EXPIRED_ID = b64encode(b'\x00\x00\x00\x00_session_id').decode('latin-1')
BADFILE_ID = b64encode(b'\xff\xff\xff\xff_session_id').decode('latin-1')

app = Application()

# session middleware
sess = Session(app, paths=('/login', '/invalid'))

__all__ = ['app', 'HTTP_HOST', 'HTTP_PORT',
           'EXPIRED_ID', 'BADFILE_ID', 'get_sid']


def get_sid(session_id, msg=b'UA'):
    if isinstance(session_id, str):
        session_id = session_id.encode('latin-1')

    return (session_id + b64encode(hmac.new(
        session_id, msg=msg, digestmod=hashlib.sha384
    ).digest())).decode('latin-1')


@app.on_worker_start
async def worker_start(**_):
    # create an expired session file /tmp/tremolo-sess/EXPIRED_ID
    with open(os.path.join(sess.path, EXPIRED_ID), 'w') as fp:
        json.dump({'sid': get_sid(EXPIRED_ID)}, fp)

    with open(os.path.join(sess.path, BADFILE_ID), 'w') as fp:
        fp.write('{badfile}')


@app.on_request
async def request_middleware(request, **_):
    session = request.ctx.session

    if session is not None and request.path == b'/login':
        session_id = request.cookies['sess'][0]

        if session_id in (EXPIRED_ID, BADFILE_ID):
            # expired/bad, must have been deleted by the session middleware
            assert not os.path.exists(os.path.join(sess.path, session_id))
        else:
            session.login()
            assert session.is_logged_in() is True
            assert os.path.isfile(session.filepath)


@app.route('^/(login|about)?$')
async def login(request, response, **_):
    session = request.ctx.session

    if session is None:
        return b'None'

    if session.is_logged_in():
        return b'OK'

    raise Forbidden


@app.on_response
async def response_middleware(request, response, **_):
    session = request.ctx.session

    if session is not None and request.path == b'/login':
        if request.cookies['sess'][0] not in (EXPIRED_ID, BADFILE_ID):
            session.logout()
            assert session.is_logged_in() is False
            assert os.path.isfile(session.filepath)

            session.delete()
            assert not os.path.exists(session.filepath)


if __name__ == '__main__':
    app.run(HTTP_HOST, port=HTTP_PORT, debug=True)
