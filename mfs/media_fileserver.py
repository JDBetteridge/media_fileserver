import os

from flask import (Flask, request, render_template,
                    make_response, send_from_directory,
                    redirect, url_for, session)
from glob import glob


host = "127.0.0.1"
port = 8080
mfs = Flask(__name__)

def get_log():
    path = os.path.join(os.getcwd(), "log", "*.csv")
    return [Path(f) for f in reversed(sorted(glob(path)))]

@mfs.route("/list")
def list():
    csvfiles = get_log()
    return render_template("nav.html", csvfiles=csvfiles)

@mfs.route("/list/<name>")
def download(name):
    path = os.path.join(os.getcwd(), "log")
    return send_from_directory(path, name, as_attachment=True)

@mfs.route("/list/raw/<name>")
def raw(name):
    path = os.path.join(os.getcwd(), "log", name)
    with open(path) as fh:
        contents = [line for line in fh.readlines()]
    return render_template("raw.html", raw=contents)

def main():
    # This allows us to use a plain HTTP callback
    # ~ os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"

    # Runs web application
    # add threaded=True
    mfs.run(debug=True, host="0.0.0.0", port=port) #ssl_context='adhoc'

if __name__ == "__main__":
    main()
