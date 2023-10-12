# tremolo-login
tremolo-login is basically an extension of [tremolo-session](https://github.com/nggit/tremolo-session).

You can use it just like tremolo-session but with additional methods like `login()`, `logout()`, and `is_logged_in()`.

## Usage
```python
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
        password = form_data['password'][0]

        if 'password' in form_data and compare_digest(password, 'mypass'):
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
```

## Installing
```
python3 -m pip install --upgrade tremolo_login
```

## Testing
Just run `python3 alltests.py`.

Or if you also want measurements with [coverage](https://coverage.readthedocs.io/):

```
coverage run alltests.py
coverage combine
coverage report
coverage html # to generate html reports
```

## License
MIT
