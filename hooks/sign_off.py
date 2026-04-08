"""Ensure the commit message contains a Signed-off-by line."""

import subprocess
import sys


def main():
    msg_file = sys.argv[1]
    name = subprocess.check_output(["git", "config", "user.name"], text=True).strip()
    email = subprocess.check_output(["git", "config", "user.email"], text=True).strip()
    sob = f"Signed-off-by: {name} <{email}>"

    with open(msg_file, "r") as f:
        contents = f.read()

    if sob not in contents:
        with open(msg_file, "a") as f:
            f.write(f"\n{sob}")


if __name__ == "__main__":
    main()
