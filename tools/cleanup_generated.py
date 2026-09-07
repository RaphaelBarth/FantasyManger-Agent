#!/usr/bin/env python3
"""Remove only generated FantasyManager output directories.

The command is intentionally conservative: it only considers direct child
directories of the supplied project root with approved output prefixes.
"""

import argparse
import shutil
from pathlib import Path


ALLOWED_PREFIXES = ("out-", "reports-", "temp")


def find_targets(root):
    """Return approved direct child directories in deterministic order."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("project root is not a directory: {}".format(root))
    return sorted(
        (
            child
            for child in root.iterdir()
            if child.is_dir() and child.name.startswith(ALLOWED_PREFIXES)
        ),
        key=lambda path: path.name.lower(),
    )


def cleanup(root, apply=False):
    """List targets and optionally remove them; return removed paths."""
    targets = find_targets(root)
    if apply:
        for target in targets:
            shutil.rmtree(target)
        return targets
    return targets


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Remove generated out/reports directories only."
    )
    parser.add_argument("--root", required=True, help="FantasyManager project root")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually remove approved directories; default is dry-run",
    )
    args = parser.parse_args(argv)

    targets = cleanup(args.root, apply=args.apply)
    mode = "removed" if args.apply else "would remove"
    print("{} {} target(s):".format(mode, len(targets)))
    for target in targets:
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
