"""Command line: ``caterpillars search`` and ``caterpillars respace``."""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from .core import load_words, respace, search


def _words(args: argparse.Namespace):
    return load_words(args.words, min_len=args.min_len, max_len=args.max_len, min_score=args.min_score)


def _limit(pairs, limit: int, reuse: int):
    """At most `limit` pairs, each word used at most `reuse` times (0 = no cap)."""
    used: Counter[str] = Counter()
    for pair in pairs:
        if reuse and any(used[w] >= reuse for w in pair.words):
            continue
        used.update(set(pair.words))
        yield pair
        limit -= 1
        if limit == 0:
            return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="caterpillars",
        description="Find letters that read as two different phrases: a ten dad / at end ad.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--words", help="word list: JSON list, one word per line, or WORD;score lines (default: bundled common words)")
    common.add_argument("--min-len", type=int, default=2, help="shortest word allowed, a and i excepted (default 2)")
    common.add_argument("--max-len", type=int, default=None, help="longest word allowed")
    common.add_argument("--min-score", type=int, default=0, help="for WORD;score lists, drop words scored below this")
    common.add_argument("--limit", type=int, default=50, help="how many to print, 0 for all (default 50)")
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("search", parents=[common], help="list caterpillars from a word list")
    s.add_argument("--max-words", type=int, default=2, help="most words on a side (default 2)")
    s.add_argument("--min-words", type=int, default=2, help="fewest words on a side (default 2)")
    s.add_argument("--reuse", type=int, default=2, help="print each word at most this many times, 0 for no cap (default 2)")

    r = sub.add_parser("respace", parents=[common], help="find other spacings of a phrase")
    r.add_argument("phrase", nargs="+", help='e.g. for ms independent')
    r.add_argument("--max-words", type=int, default=4, help="most words in a respacing (default 4)")
    r.add_argument("--shared-breaks", action="store_true", help="allow breaks in the same places as the phrase")

    args = parser.parse_args(argv)
    words = _words(args)
    if args.command == "search":
        pairs = search(words, max_words=args.max_words, min_words=args.min_words)
        shown = _limit(pairs, args.limit, args.reuse)
    else:
        pairs = respace(" ".join(args.phrase), words, max_words=args.max_words, shared_breaks=args.shared_breaks)
        shown = _limit(pairs, args.limit, 0)
    for pair in shown:
        print(pair)
    if not pairs:
        print("none found", file=sys.stderr)
        return 1
    return 0
