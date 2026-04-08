"""Verify that pushed commits authored by the current user have a Signed-off-by line."""

import subprocess
import sys


def main():
    my_email = subprocess.check_output(["git", "config", "user.email"], text=True).strip()

    for line in sys.stdin:
        parts = line.split()
        if len(parts) < 4:
            continue
        local_oid, remote_oid = parts[1], parts[3]

        null = "0" * 40
        if local_oid == null:
            continue
        rev_range = local_oid if remote_oid == null else f"{remote_oid}..{local_oid}"

        oids = (
            subprocess.check_output(["git", "rev-list", rev_range], text=True).strip().splitlines()
        )
        for oid in oids:
            author = subprocess.check_output(
                ["git", "log", "--format=%ae", "-n1", oid], text=True
            ).strip()
            if author != my_email:
                continue

            msg = subprocess.check_output(["git", "log", "--format=%B", "-n1", oid], text=True)
            if not any(line.startswith("Signed-off-by: ") for line in msg.splitlines()):
                print(f"ERROR: Commit {oid} missing Signed-off-by.")
                sys.exit(1)


if __name__ == "__main__":
    main()
