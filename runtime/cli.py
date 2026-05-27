"""Minimal CLI entrypoint registered by `pyproject.toml`.

This is *only* a stub. Subcommands will be added when the runtime gains
real operations (`migrate`, `workflow start`, `agent list`, …).
"""

from __future__ import annotations

import sys


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print(_HELP)
        return 0
    print(f"unknown command: {args[0]}", file=sys.stderr)
    print(_HELP, file=sys.stderr)
    return 2


_HELP = """\
aine — AI-Native Engineering Platform

Usage:
  aine --help          Show this message.

(scaffolding — subcommands are intentionally not implemented yet)
"""
