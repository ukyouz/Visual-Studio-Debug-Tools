import os
import subprocess
import textwrap
from argparse import ArgumentParser


def get_sha():
    sha = subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=os.path.dirname(__file__),
    )
    return sha.decode().rstrip()


def get_timestamp(sha: str) -> str:
    timestamp = subprocess.check_output(
        [
            "git",
            "show",
            "--no-patch",
            "--format=%ci",
            sha,
        ],
        cwd=os.path.dirname(__file__),
    )

    return timestamp.decode().rstrip()


def main(version, out_dir):
    commit = get_sha()
    timestamp = get_timestamp(commit)

    txt = textwrap.dedent("""
        Version: {}
        Commit: {}
        Date: {}
    """.format(
        version,
        commit,
        timestamp,
    )).strip()

    with open(os.path.join(out_dir, "about_me.txt"), "w") as fs:
        fs.write(txt)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "version",
        default="test",
    )
    parser.add_argument(
        "--out_dir",
        default=os.path.dirname(__file__),
    )
    args = parser.parse_args()

    main(args.version, args.out_dir)
