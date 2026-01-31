# tremolo-login
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=nggit_tremolo-login&metric=coverage)](https://sonarcloud.io/summary/new_code?id=nggit_tremolo-login)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=nggit_tremolo-login&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=nggit_tremolo-login)

tremolo-login is basically an extension of [tremolo-session](https://github.com/nggit/tremolo-session).

You can use it just like tremolo-session but with additional methods like `login()`, `logout()`, and `is_logged_in()`.

## Usage
```python
#!/usr/bin/env python3

from hmac import compare_digest

from tremolo import Application
from tremolo_login import Session

app = Application()

# this is a session middleware
# that enables you to use request.ctx.session
Session(app, expires=1800)


@app.route('/')
async def index(request, **server):
    session = request.ctx.session

    if session is None or not session.is_logged_in():
        return b'You are not logged in. <a href="/login">Login</a>.'

    return b'Welcome to Dashboard. <a href="/logout">Logout</a>.'


@app.route('/login')
async def login(request, **server):
    session = request.ctx.session

    if request.method == b'POST':
        form_data = await request.form()

        if ('password' in form_data and
                compare_digest(form_data['password'][0], 'mypass')):
            # password match! set current session as logged in:
            session.login()
            # the return value is a `token`, if you want to use
            # `Authorization: Bearer <token>`

            return b'Login success! Go to <a href="/">Dashboard</a>.'

    return (b'<form action="/login" method="post"><div>'
            b'<label for="password">Password:</label> '
            b'<input type="text" name="password" placeholder="mypass" /> '
            b'<input type="submit" value="Login" /></div>'
            b'</form>')


@app.route('/logout')
async def logout(request, response, **server):
    session = request.ctx.session

    session.logout()

    # if you want the session data to be deleted:
    # the session id will also rotate on the next login
    # session.delete()

    response.set_status(302, b'Found')
    response.set_header(b'Location', b'/')

    return b''


if __name__ == '__main__':
    app.run('0.0.0.0', 8000, debug=True, reload=True)
```

## Installing
```
python3 -m pip install --upgrade tremolo_login
```

## Testing
Just run `python3 -m tests`.

Or if you also want measurements with [coverage](https://coverage.readthedocs.io/):

```
coverage run -m tests
coverage combine
coverage report
coverage html # to generate html reports
```

## License
MIT License
