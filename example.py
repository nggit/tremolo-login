#!/usr/bin/env python3

from hmac import compare_digest

from tremolo import Tremolo
from tremolo_login import Session

app = Tremolo()

# this is a session middleware
# that enables you to use context.session or request.context.session
Session(app, expires=1800)


@app.route('/')
async def index(request=None, **server):
    session = request.context.session

    if session is None or not session.is_logged_in():
        return b'You are not logged in. <a href="/login">Login</a>.'

    return b'Welcome to Dashboard. <a href="/logout">Logout</a>.'


@app.route('/login')
async def login(request=None, **server):
    session = request.context.session

    if request.method == b'POST':
        form_data = await request.form()

        if ('password' in form_data and
                compare_digest(form_data['password'][0], 'mypass')):
            # password match! set current session as logged in
            session.login()
            return b'Login success! Go to <a href="/">Dashboard</a>.'

    return (b'<form action="/login" method="post"><div>'
            b'<label for="password">Password:</label> '
            b'<input type="text" name="password" placeholder="mypass" /> '
            b'<input type="submit" value="Login" /></div>'
            b'</form>')


@app.route('/logout')
async def logout(request=None, response=None, **server):
    session = request.context.session

    session.logout()

    response.set_status(302, b'Found')
    response.set_header(b'Location', b'/')

    return b''

if __name__ == '__main__':
    app.run('0.0.0.0', 8000, debug=True)
