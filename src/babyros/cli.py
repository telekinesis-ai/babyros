"""
Command-line interface for BabyROS, installed as the ``babyros`` script.
"""

import argparse
import sys

from babyros import configure
from babyros.node import list_topics


def _split(key: str) -> tuple[str, str]:
    """Split a "babyros/<kind>/<topic>" token key into its kind and topic."""
    _, kind, topic = key.split("/", 2)
    return kind, topic


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``babyros`` console script."""
    parser = argparse.ArgumentParser(
        prog="babyros", description="Inspect a running BabyROS network."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_cmd = subparsers.add_parser(
        "list",
        help="Watch the topics that live BabyROS nodes are using.",
        description=(
            "Print the topics that live BabyROS nodes are using, then keep "
            "watching and report nodes as they come and go, until Ctrl+C."
        ),
    )
    list_cmd.add_argument(
        "key_expr",
        nargs="?",
        default="**",
        help=(
            "Key expression to match, relative to the 'babyros/' prefix that "
            "is always prepended. Tokens are '<kind>/<topic>', so "
            "'publisher/**' lists only publisher topics and '*/robot/**' "
            "every topic under 'robot'. Default '**' (everything)."
        ),
    )
    list_cmd.add_argument(
        "-1",
        "--once",
        action="store_true",
        help="Print the topics that are live right now and exit.",
    )
    list_cmd.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=1.0,
        help="Seconds to wait for replies with --once. Default 1.0.",
    )

    args = parser.parse_args(argv)

    # This process is short-lived: without waiting for scouted peers to be
    # connected, the query goes out before anyone can answer it and the
    # listing comes back empty most of the time.
    configure(open_return_conditions_connect_scouted=True)

    if not args.once:
        print(f"Watching babyros/{args.key_expr}  (Ctrl+C to stop)", file=sys.stderr)

    try:
        for online, key in list_topics(
            args.key_expr, watch=not args.once, timeout=args.timeout
        ):
            kind, topic = _split(key)
            state = "" if args.once else f"{'ONLINE ' if online else 'OFFLINE'}  "
            print(f"{state}{kind:<10} {topic}", flush=True)
    except KeyboardInterrupt:
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
