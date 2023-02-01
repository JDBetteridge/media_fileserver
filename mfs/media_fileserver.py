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
    def __init__(self, path, rel_to=directory):
        if isinstance(path, Path):
            self.path = path
        else:
            self.path = Path(path)
        self.name = self.path.name
        self.pathstr = str(self.path.absolute().relative_to(rel_to))
        self.html = str(escape(self.pathstr))
        self.quote = quote(self.pathstr)
        self.filename = secure_filename(self.pathstr)

    def __repr__(self):
        rep = f"<SafePathName({self.path!r})>"
        rep += f"\n\tHTML    : {self.html!r}"
        rep += f"\n\tquote   : {self.quote!r}"
        rep += f"\n\tsecurefn: {self.filename!r}"
        return rep


def get_files(path):
    directories = []
    files = []
    for f in sorted(path.glob("*")):
        if f.is_dir():
            directories.append(SafePathName(f))
        else:
            files.append(SafePathName(f))
    return directories + files


@mfs.route("/")
@mfs.route("/<path:path>")
def list2(path="."):
    filelist = get_files(directory/Path(path))
    safepath = SafePathName(directory/path)
    parent = SafePathName(safepath.path.parent) if safepath.path != directory else None
    if safepath.path == directory:
        safepath = None
    return render_template("nav.html", path=safepath, parent=parent, filelist=filelist)


@mfs.route("/download/<path:path>/<name>")
def download(path, name):
    return send_from_directory(directory/path, name, as_attachment=True)


@mfs.route("/raw/<path:path>/<name>")
def raw(path, name):
    ext = Path(name).suffix
    if ext:
        ext = ext[1:]
    if ext in ["mp4", "mkv"]:
        return send_from_directory(directory/path, name, as_attachment=False, mimetype="video/" + ext)
    elif ext in ["jpg", "jpeg", "png"]:
        return send_from_directory(directory/path, name, as_attachment=False, mimetype="image/" + ext)
    elif ext in ["pdf"]:
        return send_from_directory(directory/path, name, as_attachment=False, mimetype="application/" + ext)
    elif ext in ["txt", "srt", ""]:
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
