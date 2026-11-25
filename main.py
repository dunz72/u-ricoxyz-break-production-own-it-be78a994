#!/usr/bin/env python3
"""Deliver the Break Production, Own It one-liner to the grading folder.

The entry is a single 127-character line stored in entry.txt next to this
file. This program reads those bytes, checks the one-line rules, drops an
untouched copy into $MAKEFUN_OUTPUT_DIR (or /output when that variable is
absent), then reads the copy back and compares SHA-256 digests so a
corrupt write fails loudly here instead of on the grader.

Standard library only: the grading image ships no third-party packages.
"""

import hashlib
import os
import sys
from pathlib import Path

LOWER_BOUND = 1
UPPER_BOUND = 200
FALLBACK_DIR = "/output"
ENTRY_NAME = "entry.txt"


def abort(reason):
    """Report a fatal problem on stderr and stop with status 1."""
    sys.stderr.write("error: %s\n" % reason)
    raise SystemExit(1)


def script_folder():
    """Folder containing this script, resolved to an absolute path."""
    return Path(__file__).resolve().parent


def fetch_entry_bytes():
    """Return the raw bytes of entry.txt beside this script."""
    entry_path = script_folder() / ENTRY_NAME
    try:
        return entry_path.read_bytes()
    except OSError as problem:
        abort("cannot read %s: %s" % (entry_path, problem))


def to_text(payload):
    """Interpret payload as UTF-8 text, aborting on bad encoding."""
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        abort("entry.txt is not valid UTF-8")


def rule_checks(text):
    """Yield (broken, message) pairs for every one-line rule."""
    yield "\r" in text or "\n" in text, (
        "entry.txt must hold exactly one line, no line breaks"
    )
    yield len(text) < LOWER_BOUND, "entry.txt is empty"
    yield len(text) > UPPER_BOUND, (
        "entry is %d chars, limit is %d" % (len(text), UPPER_BOUND)
    )
    yield text.strip() != text, (
        "entry.txt must not start or end with whitespace"
    )
    yield not text.strip(), "entry.txt must not be blank"
    yield "\t" in text, "entry.txt must not contain tab characters"
    yield "  " in text, "entry.txt must not contain double spaces"
    yield any(
        ord(symbol) < 0x20 or ord(symbol) == 0x7F for symbol in text
    ), "entry.txt must not contain control characters"


def enforce_rules(text):
    """Abort on the first broken one-line rule, if any."""
    for broken, message in rule_checks(text):
        if broken:
            abort(message)


def destination_folder():
    """Output folder from the environment, falling back to /output."""
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or FALLBACK_DIR)


def prepare_folder(folder):
    """Create folder and parents when they do not exist yet."""
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as problem:
        abort("cannot create output dir %s: %s" % (folder, problem))


def store_copy(path, payload):
    """Write payload bytes to path."""
    try:
        path.write_bytes(payload)
    except OSError as problem:
        abort("cannot write %s: %s" % (path, problem))


def fingerprint(payload):
    """SHA-256 hex digest of payload bytes."""
    return hashlib.sha256(payload).hexdigest()


def confirm_copy(path, wanted, byte_count):
    """Re-read path and abort unless size and digest match the source."""
    try:
        copied = path.read_bytes()
    except OSError as problem:
        abort("cannot re-read %s: %s" % (path, problem))
    if len(copied) != byte_count:
        abort(
            "output is %d bytes, expected %d" % (len(copied), byte_count)
        )
    if fingerprint(copied) != wanted:
        abort("output differs from entry.txt (sha256 mismatch)")


def run():
    payload = fetch_entry_bytes()
    text = to_text(payload)
    enforce_rules(text)

    folder = destination_folder()
    prepare_folder(folder)
    target = folder / ENTRY_NAME
    store_copy(target, payload)
    digest = fingerprint(payload)
    confirm_copy(target, digest, len(payload))

    print(
        "wrote %d bytes, %d chars -> %s"
        % (len(payload), len(text), target)
    )
    print("sha256: %s" % digest)


if __name__ == "__main__":
    run()
