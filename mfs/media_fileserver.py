import os

from flask import (Flask, request, render_template,
                    make_response, send_from_directory,
                    redirect, url_for, session, escape)
# ~ from glob import glob
from pathlib import Path
from urllib.parse import quote, unquote
from werkzeug.utils import secure_filename

host = "127.0.0.1"
port = 8080
mfs = Flask(__name__)
directory = Path("/srv/torrents")


class SafePathName:
    def __init__(self, path):
        if isinstance(path, Path):
            self.path = path
        else:
            self.path = Path(path)
        self.name = self.path.name
        self.html = str(escape(self.name))
        self.quote = quote(self.name)
        self.filename = secure_filename(self.name)


def get_files(path):
    return [SafePathName(f) for f in sorted(path.glob("*"))]


# ~ @mfs.route("/")
# ~ def list():
    # ~ filelist = get_files(directory)
    # ~ return render_template("nav.html", filelist=filelist)

@mfs.route("/")
@mfs.route("/<path:path>")
def list2(path="."):
    print(path)
    filelist = get_files(directory/Path(path))
    safepath = SafePathName(path)
    parent = SafePathName(safepath.path.parent) if path != "." else None
    return render_template("nav.html", path=safepath, parent=parent, filelist=filelist)


@mfs.route("/download/<path:path>/<name>")
def download(path, name):
    return send_from_directory(directory/path, name, as_attachment=True)


# ~ @mfs.route("/raw/<name>")
# ~ def raw(name):
    # ~ path = directory/name
    # ~ print(path, flush=True)
    # ~ with open(path) as fh:
        # ~ contents = [line for line in fh.readlines()]
    # ~ return render_template("raw.html", raw=contents)
@mfs.route("/raw/<path:path>/<name>")
def raw(path, name):
    # ~ path = directory/name
    # ~ with open(path) as fh:
        # ~ contents = [line for line in fh.readlines()]
    ext = Path(name).suffix
    if ext:
        ext = ext[1:]
    if ext in ["mp4"]:
        return send_from_directory(directory/path, name, as_attachment=False, mimetype="video/" + ext)
    elif ext in ["txt", ""]:
        with open(directory/path/name) as fh:
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
