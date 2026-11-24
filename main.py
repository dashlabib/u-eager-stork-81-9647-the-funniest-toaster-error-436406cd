#!/usr/bin/env python3
"""Publish the one-line entry for the make.fun bounty
"The Funniest Toaster Error Message".

The error message lives in ``entry.txt`` next to this file. This
program reads it, checks it against the bounty gate (UTF-8 text, a
single line, 1 to 120 characters, not only white space, and it must
read as a real appliance error message), writes the exact bytes to
``entry.txt`` in the output directory, and reads the published file
back to confirm the published bytes match the source byte for byte.
Standard library only: no network access, no clock reads, no
randomness, so two runs always produce identical output.

The output directory is ``$MAKEFUN_OUTPUT_DIR`` when set, else
``/output``. Pass ``--output-dir <dir>`` to choose it on the command
line instead, or ``--verify-only`` to check the message without
writing anything.
"""

import argparse
import os
import sys
from pathlib import Path

MAX_CHARS = 120
DEFAULT_OUTPUT_DIR = "/output"

ERROR_PREFIXES = ("ERROR", "ERR ", "FAULT", "WARNING")


def entry_path() -> Path:
    """Return the path of the ``entry.txt`` shipped with this program."""
    return Path(__file__).resolve().parent / "entry.txt"


def load_raw() -> bytes:
    """Read the entry file as raw bytes, verbatim.

    The bytes are published exactly as stored, trailing newline
    included, so the output is byte-identical to the source file.
    """
    try:
        return entry_path().read_bytes()
    except FileNotFoundError:
        raise SystemExit(f"entry file not found: {entry_path()}")
    except OSError as exc:
        raise SystemExit(f"cannot read entry file {entry_path()}: {exc}")


def decode_entry(raw: bytes) -> str:
    """Decode the raw entry bytes as UTF-8 and strip the line ending.

    Only the file's trailing newline is formatting; any other
    surrounding whitespace is part of the entry and is rejected
    by validate() below, so a stray space cannot slip through.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit("entry is not valid UTF-8 text")
    return text.rstrip("\r\n")


def load_message() -> str:
    """Load and decode the entry text for validation."""
    return decode_entry(load_raw())


def validate(text: str, max_chars: int = MAX_CHARS) -> None:
    """Check the entry against the bounty gate, raising SystemExit."""
    if not text or text.isspace():
        raise SystemExit(
            "error: entry is empty or only white space "
            "(entry.txt must hold one non-blank line)"
        )
    if text != text.strip():
        raise SystemExit(
            "error: entry has leading or trailing whitespace "
            "(remove the stray space at the start or end of the line)"
        )
    if "\t" in text:
        raise SystemExit("entry must not contain tab characters")
    if len(text) > max_chars:
        raise SystemExit(
            f"entry is {len(text)} characters, over the {max_chars} limit"
        )
    if "\n" in text or "\r" in text:
        raise SystemExit("entry must be a single line")
    # The joke only lands if the error is about the toaster's own
    # job: refuse a generic error line that never mentions bread
    # or toast at all.
    lowered = text.lower()
    if "bread" not in lowered and "toast" not in lowered:
        raise SystemExit(
            "entry does not mention bread or toast "
            "(a toaster error should be about its own job)"
        )
    # The judge's first criterion is that the line reads like a real
    # error message a kitchen toaster would show its owner: refuse a
    # joke that does not present itself as an appliance error.
    if not text.startswith(ERROR_PREFIXES):
        raise SystemExit(
            "entry does not read as an appliance error message "
            f"(must start with one of: {', '.join(ERROR_PREFIXES)})"
        )


def resolve_output_dir(args) -> Path:
    """Pick the output directory: flag wins, then env, then default."""
    chosen = args.output_dir or os.environ.get(
        "MAKEFUN_OUTPUT_DIR", DEFAULT_OUTPUT_DIR
    )
    return Path(chosen)


def publish(raw: bytes, out_dir: Path) -> Path:
    """Write the raw entry bytes verbatim and verify the round trip.

    Returns the path written. The published file is read back and
    compared byte for byte with the source, so a short write or a
    stray newline translation is caught instead of silently shipped.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.txt"
    out_path.write_bytes(raw)
    published = out_path.read_bytes()
    if published != raw:
        raise SystemExit(
            f"published entry does not match entry.txt "
            f"({len(published)} bytes written, {len(raw)} expected)"
        )
    return out_path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="directory to write entry.txt into",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the message without writing it",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=MAX_CHARS,
        help=f"maximum entry length in characters (default {MAX_CHARS})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print nothing on success",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.max_chars < 1:
        raise SystemExit("--max-chars must be at least 1")
    raw = load_raw()
    text = decode_entry(raw)
    validate(text, max_chars=args.max_chars)
    if args.verify_only:
        if not args.quiet:
            print(f"Valid: {len(text)} characters")
        return 0
    out_path = publish(raw, resolve_output_dir(args))
    if not args.quiet:
        print(f"Wrote {len(raw)} bytes ({len(text)} characters) to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
