from flask import Flask
from flask import request
import pytz
import local_settings as conf

__doc__ = """\
ping.py
   Basic flask application to respond to a slash command in Mattermost
"""

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
            APIError("No Token", status_code=401)
        if conf.AUTH_TKN not in request.headers['Authorization']:
            APIError("Not Authorized", status_code=401)
        return func
    return _wrapper


def do_convert(tz_to_convert):
    pytz.all_timezones
    user_tz = tz_to_convert
    datetime.now(timezone(user_tz)).strftime(format)


@authorized
@app.route("/slash", methods=["POST"])
def slash():
    from pprint import pprint, pformat
    import re

    ret = ""

    if request.form['text'] == "help":
        ret += pformat(pytz.all_timezones, indent=4)

    elif re.match(r'convert', request.form['text'], re.I):
        do_convert(re.compile('\W+').split(request.form['text'])[1:])
        ret += pformat(re.compile('\W+').split(request.form['text']))

    else:
        ret += pformat("PONG! %s" % pformat(re.compile('\W+').split(request.form['text'])))

    return (ret)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
