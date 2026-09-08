#!/usr/bin/env python3
"""Remove only generated FantasyManager output directories and lineups.

The command is intentionally conservative: it only considers direct child
directories with approved output prefixes and direct lineup markdown files.
"""

import argparse
import shutil
from pathlib import Path


ALLOWED_PREFIXES = ("out-", "reports-", "temp")
LINEUP_PREFIX = "lineup-"


def find_targets(root):
    """Return approved direct output paths in deterministic order."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("project root is not a directory: {}".format(root))
    return sorted(
        (
            child
            for child in root.iterdir()
            if (
                (child.is_dir() and child.name.startswith(ALLOWED_PREFIXES))
                or (
                    child.is_file()
                    and child.name.startswith(LINEUP_PREFIX)
                    and child.suffix == ".md"
                )
            )
        ),
        key=lambda path: path.name.lower(),
    )


def caretaker(root, apply=False):
    """List targets and optionally remove them; return removed paths."""
    targets = find_targets(root)
    if apply:
        for target in targets:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        return targets
    return targets


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Remove generated out/reports directories and lineup reports."
    )
    parser.add_argument("--root", required=True, help="FantasyManager project root")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually remove approved directories; default is dry-run",
    )
    args = parser.parse_args(argv)

    targets = caretaker(args.root, apply=args.apply)
    mode = "removed" if args.apply else "would remove"
    print("{} {} target(s):".format(mode, len(targets)))
    for target in targets:
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
