# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Anggit Arfanto

import hashlib
import hmac
import json
import os
import tempfile
import time

from base64 import b64decode, urlsafe_b64encode as b64encode

from tremolo.exceptions import BadRequest, Forbidden

__version__ = '1.1.0'
__all__ = ['Session']


def now():
    return int(time.time()) & 0xffffffff


def get_exp_time(session_id):
    """The first 4 bytes of the raw `session_id` is the expiration time."""
    return int.from_bytes(
        b64decode(session_id, altchars=b'-_', validate=True)[:4],
        byteorder='big'
    )


class Session:
    def __init__(self, app, name='sess', path='sess', paths=(),
                 expires=1800, cookie_params={}):
        """A simple, file-based session middleware for Tremolo.

        :param app: The Tremolo app object
        :param name: Session name. Will be used in the response header. E.g.
            ``Set-Cookie: sess=Base64stringHere;``
        :param path: A session directory path where the session files will be
            stored. E.g. ``/path/to/dir``. If it doesn't exist, it will be
            created under the Operating System temporary directory.
        :param paths: A list of url path prefixes
            where the ``Set-Cookie`` header should appear.
            ``['/']`` will match ``/any``,
            ``['/users']`` will match ``/users/login``, etc.
        """
        self.name = name
        self.path = self._get_path(path, app.__class__.__name__)
        self.paths = {v.rstrip('/').encode('latin-1') for v in paths}
        self.expires = min(expires, 31968000)

        # overwrite to maximum cookie validity (400 days)
        cookie_params['expires'] = 34560000

        self.cookie_params = cookie_params

        app.add_middleware(self._on_request, 'request')
        app.add_middleware(self._on_response, 'response')

    def _get_path(self, path, prefix):
        if os.path.isdir(path):
            return path

        tmp = tempfile.mkdtemp()
        os.rmdir(tmp)
        tmp = os.path.join(
            os.path.dirname(tmp), '%s-%s' % (prefix.lower(),
                                             os.path.basename(path))
        )

        if not os.path.exists(tmp):
            os.mkdir(tmp)

        return tmp

    def _regenerate_id(self, request, length=16 * 3):
        for i in range(2):
            session_id = b64encode(
                request.uid(length, ts_offset=self.expires + i)
            ).decode('latin-1')

            if not os.path.exists(os.path.join(self.path, session_id)):
                return session_id

        raise FileExistsError('session id collision')

    async def _on_request(self, request, response, **_):
        request.ctx.session = None
        path = request.path.rstrip(b'/')
        depth = 0

        while depth < 255:
            if not self.paths or path in self.paths:
                break

            end = path.rfind(b'/')

            if end == -1:
                return

            path = path[:end]
            depth += 1
        else:
            return

        response.set_header(b'Cache-Control', b'no-cache, must-revalidate')
        response.set_header(b'Expires', b'Thu, 01 Jan 1970 00:00:00 GMT')

        if b'authorization' in request.headers:
            p, _, token = request.headers[b'authorization'][0].partition(b' ')

            if p.lower() != b'bearer':
                raise BadRequest('missing Bearer prefix')

            session_id = token[:-64].lstrip(b' /').decode('latin-1')
            sid = token[-64:].decode('latin-1')
        elif self.name in request.cookies:
            session_id = request.cookies[self.name][0].lstrip('/')
            sid = None
        else:
            response.set_cookie(self.name, self._regenerate_id(request),
                                **self.cookie_params)
            return

        try:
            expires = get_exp_time(session_id)
        except ValueError as exc:
            response.set_cookie(self.name, self._regenerate_id(request),
                                **self.cookie_params)

            raise Forbidden(
                'invalid token',
                set_cookie=response.headers[b'set-cookie'][-1]
            ) from exc

        session_filepath = os.path.join(self.path, session_id)
        session = {}

        if os.path.isfile(session_filepath):
            if now() > expires:
                os.unlink(session_filepath)
            else:
                with open(session_filepath, 'r') as fp:
                    data = fp.read()

                try:
                    session.update(json.loads(data))
                except ValueError:
                    os.unlink(session_filepath)

        if not os.path.isfile(session_filepath):
            session_id = self._regenerate_id(request)
            session_filepath = os.path.join(self.path, session_id)

        request.ctx.session = SessionData(self,
                                          session_id,
                                          sid,
                                          session,
                                          session_filepath,
                                          request)

        # always renew/update session and cookie expiration time
        response.set_cookie(self.name, session_id, **self.cookie_params)

    async def _on_response(self, request, **_):
        if request.ctx.session is not None:
            request.ctx.session.save()


class SessionData(dict):
    def __init__(self, sess, session_id, sid, session, filepath, request):
        self.name = sess.name
        self.path = sess.path
        self.id = session_id
        self.sid = sid
        self.session = session
        self.filepath = filepath
        self.request = request

        self.update(session)

    def save(self):
        if self != self.session:
            self.session.clear()
            self.session.update(self)

            with open(self.filepath, 'w') as fp:
                json.dump(self, fp)

    def delete(self):
        self.clear()
        self.session.clear()

        if os.path.exists(self.filepath):
            os.unlink(self.filepath)

    def get_token(self, msg=b''):
        if not msg and b'user-agent' in self.request.headers:
            msg = self.request.headers[b'user-agent'][0]

        try:
            return self.id + b64encode(hmac.digest(
                self.id.encode('latin-1'),
                msg,
                hashlib.sha384
            )).decode('latin-1')
        except AttributeError:
            return self.id + b64encode(hmac.new(
                self.id.encode('latin-1'),
                msg=msg,
                digestmod=hashlib.sha384
            ).digest()).decode('latin-1')

    def login(self, msg=b''):
        token = self.get_token(msg)
        self['sid'] = self.sid or token[-64:]
        self.save()

        return token

    def logout(self):
        if 'sid' in self:
            del self['sid']
            self.save()

    def is_logged_in(self, msg=b''):
        sid = self.sid or self.get_token(msg)[-64:]
        return 'sid' in self and hmac.compare_digest(sid, self['sid'])
