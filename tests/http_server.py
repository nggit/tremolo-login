#!/usr/bin/env python3

__all__ = ('app', 'HTTP_HOST', 'HTTP_PORT')

import hashlib  # noqa: E402
import hmac  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

# makes imports relative from the repo directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tremolo import Application  # noqa: E402
from tremolo.exceptions import Forbidden  # noqa: E402
from tremolo_login import Session  # noqa: E402

HTTP_HOST = '127.0.0.1'
HTTP_PORT = 28000

app = Application()

# session middleware
sess = Session(app)

_SIGNATURE = hmac.new(
    bytes.fromhex('5e55'), msg=b'UA', digestmod=hashlib.sha256
).hexdigest()


@app.on_worker_start
async def worker_start(**_):
    # create file /tmp/tremolo-sess/5e55
    with open(os.path.join(sess.path, '5e55'), 'w') as fp:
        json.dump({'_login': _SIGNATURE}, fp)


@app.on_request
async def request_middleware(request, **_):
    session = request.ctx.session

    if session is not None:
        if '5e55.' not in request.cookies['sess'][0]:
            session.login()
            assert session.is_logged_in() is True

            session.logout()
            assert session.is_logged_in() is False


@app.route('/')
async def index(request, response, **_):
    session = request.ctx.session

    if session is None or not session.is_logged_in():
        raise Forbidden

    return b'OK'


@app.on_response
async def response_middleware(request, response, **_):
    session = request.ctx.session

    if session is not None:
        if '5e55.' in request.cookies['sess'][0]:
            session.delete()


if __name__ == '__main__':
    app.run(HTTP_HOST, port=HTTP_PORT, debug=True)
