from mattermostdriver import Driver
from flask import Flask, request, abort
import flask
from datetime import datetime
import pytz
from pprint import pprint, pformat
import re
import local_settings as conf

__doc__ = """\
ping.py
   Basic flask application to respond to a slash command in Mattermost
"""

mm = Driver({'url': conf.MM_HOST,
             'token': conf.MM_TOKEN,
             'scheme': conf.MM_SCHEME,
             'port': conf.MM_PORT,
             'basepath': '/api/v4',
             'verify': True})
mm.login()
app = Flask(__name__)


class APIError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
                self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(APIError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def authorized(func):
    def _wrapper(*args, **kwargs):
        if 'Authorization' not in request.headers:
            print('no token')
            APIError("No Token", status_code=401)
            flask.abort(401, "No Token")
        if request.headers['Authorization'] not in conf.AUTH_TKN:
            print('token invalid')
            APIError("Not Authorized", status_code=401)
            flask.abort(401, "Not Authorized")
        return func(*args, **kwargs)
    return _wrapper


def my_dec(func):
    def wrapper(*org_args, **org_kwargs):
        from pprint import pprint as pp
        pp(request.headers)
        return func(*org_args, **org_kwargs)
    return wrapper


def do_convert(users):
    ret = ""
    mm_users = mm.users.get_users()

    if users is None:
        users = [x['username'] for x in mm_users]
    else:
        users = re.sub(r'@', '', users).split()

    intersect_users = list(filter(set([x['username'] for x in mm_users]).__contains__, users))
    not_found_users = list(set(users).difference(intersect_users))

    if not_found_users:
        ret += "Users not found: @" + ' @'.join(not_found_users) + "\n"

    convert_users = [x for x in mm_users if x['username'] in intersect_users]
    for user in convert_users:
        tz = user['position']
        if tz in pytz.all_timezones:
            date = datetime.now(pytz.timezone(tz)).strftime(conf.TIME_FMT)
        else:
            date = "invalid tz"
        ret += '@%s localtime %s\n' % (user['username'], date)

    return ret


@app.route("/localtime", methods=["POST"])
@authorized
def slash():

    ret = ""

    if request.form['text'] == "help":
        ret = pformat(pytz.all_timezones, indent=4)

    elif request.form['text'] == "all":
        ret = do_convert(None)

    else:
        ret = do_convert(request.form['text'])

    return (ret)


@app.route('/poll', methods=["POST"])
def poll():
    from pprint import pformat
    ret = ''
    # ret += pformat(request.form['text'])
    ret += pformat(request.headers)
    # ret += "\n" + pformat(request.headers, indent=4)
    print (ret)
    return (ret)


if __name__ == '__main__':
    app.run(port=5001, debug=True)
