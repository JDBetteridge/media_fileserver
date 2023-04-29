import io
import os
import tarfile

from argparse import ArgumentParser
from flask import (Flask, Blueprint, render_template, send_from_directory,
                   send_file, escape)
from functools import partial
from pathlib import Path
from urllib.parse import quote
from werkzeug.utils import secure_filename

mfs = Flask(__name__)
browse = Blueprint('name', __name__)


class SafePathName:
    def __init__(self, path, rel_to=None):
        if rel_to is None:
            rel_to = mfs.config["directory"]
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


@browse.route("/")
@browse.route("/<path:path>")
def list2(path="."):
    directory = mfs.config["directory"]
    filelist = get_files(directory/Path(path))
    safepath = SafePathName(directory/path)
    if safepath.path != directory:
        parent = SafePathName(safepath.path.parent)
    else:
        parent = None
    if safepath.path == directory:
        safepath = None
    return render_template(
        "nav.html",
        prefix=mfs.config["url_prefix"],
        path=safepath,
        parent=parent,
        filelist=filelist
    )


@browse.route("/download/<name>")
@browse.route("/download/<path:path>/<name>")
def download(name, path="."):
    IN_MEMORY = False
    directory = mfs.config["directory"]
    if (directory/path/name).is_dir():
        # Set filename and source
        if name:
            filename = secure_filename(name)
            source_dir = directory/path/name
        else:
            filename = secure_filename(Path(path).stem)
            source_dir = directory/path
        filename += ".tgz"

        # Use memory or disk as a buffer
        exists = False
        if IN_MEMORY:
            buffer_ctx = io.BytesIO()
        else:
            cache_dir = Path(".cache")
            os.makedirs(cache_dir, exist_ok=True)
            output = cache_dir/filename
            if output.exists():
                buffer_ctx = open(output, "r+b")
                exists = True
            else:
                buffer_ctx = open(output, "w+b")

        # Tarball everything
        if not exists:
            with tarfile.open(None, "w:gz", fileobj=buffer_ctx) as tar:
                tar.add(source_dir, arcname="")
            # Rewind the buffer
            buffer_ctx.seek(0)

        # send_file() will close the buffer context for us
        return send_file(
            buffer_ctx, download_name=filename, as_attachment=True
        )

    else:
        return send_from_directory(directory/path, name, as_attachment=True)


@browse.route("/raw/<name>")
@browse.route("/raw/<path:path>/<name>")
def raw(name, path="."):
    directory = mfs.config["directory"]
    ext = Path(name).suffix
    if ext:
        ext = ext[1:]
    sfd = partial(
        send_from_directory, directory/path, name, as_attachment=False
    )
    if ext in ["mp4", "mkv"]:
        return sfd(mimetype="video/" + ext)
    elif ext in ["jpg", "jpeg", "png"]:
        return sfd(mimetype="image/" + ext)
    elif ext in ["pdf"]:
        return sfd(mimetype="application/" + ext)
    elif ext in ["txt", "srt", ""]:
        with open(directory/path/name) as fh:
            contents = [line for line in fh.readlines()]
        return render_template(
            "raw.html",
            prefix=mfs.config["url_prefix"],
            raw=contents
        )


def main(args):
    # Register the blueprint at URL subdirectory args.prefix,
    # but only if running directly with flask
    browse.static_folder = "static"
    mfs.register_blueprint(
        browse,
        url_prefix=args.prefix,
    )
    # Otherwise uWSGI app is added at URL subdirectory by lighttpd (see ***)

    # Runs web application
    mfs.run(debug=True, host="0.0.0.0", port=args.port)


# Command line arguments
parser = ArgumentParser()
parser.add_argument(
    "--prefix",
    type=str,
    help="web address prefix to prepend",
    default=""
)
parser.add_argument(
    "--serve",
    type=str,
    help="directory to serve",
    default="."
)
parser.add_argument(
    "--port",
    type=int,
    help="port to serve website on",
    default=8080
)
args, _ = parser.parse_known_args()

mfs.config["directory"] = Path(args.serve).absolute()
mfs.config["url_prefix"] = args.prefix

if __name__ == "__main__":
    main(args)
else:
    # (***)
    mfs.register_blueprint(browse)
