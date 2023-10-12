# Copyright (c) 2023 nggit

__all__ = ('Session',)

import hashlib  # noqa: E402
import hmac  # noqa: E402

import tremolo_session  # noqa: E402

Session = tremolo_session.Session


class SessionData(tremolo_session.SessionData):
    def get_digest(self):
        try:
            return hmac.digest(
                self.id.encode('latin-1'),
                self.request.headers.get(b'user-agent', b''),
                hashlib.sha256).hex()
        except AttributeError:
            return hmac.new(
                self.id.encode('latin-1'),
                msg=self.request.headers.get(b'user-agent', b''),
                digestmod=hashlib.sha256
            ).hexdigest()

    def login(self):
        self['_login'] = self.get_digest()

        return self['_login']

    def logout(self):
        if '_login' in self:
            del self['_login']

    def is_logged_in(self):
        if '_login' not in self:
            return False

        return hmac.compare_digest(self['_login'], self.get_digest())


tremolo_session.SessionData = SessionData
