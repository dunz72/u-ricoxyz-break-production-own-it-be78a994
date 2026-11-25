#!/usr/bin/env python3
"""Copy the Break Production, Own It entry into the grading output dir.

The competition wants one line, 127 characters in our case, delivered as
entry.txt inside $MAKEFUN_OUTPUT_DIR (falling back to /output). This
script loads entry.txt from its own folder, validates the single-line
gate, copies the bytes untouched, then re-reads the copy and checks the
SHA-256 so a bad write is caught here, not on the grader.

Only the standard library is used: the grading image has no
third-party packages installed.
"""

import hashlib
import os
import sys

MAX_CHARS = 200
MIN_CHARS = 1


def fail(message):
    """Print message to stderr and exit non-zero."""
    sys.stderr.write("error: %s\n" % message)
    raise SystemExit(1)


def here():
    """Absolute path of the folder holding this script."""
    return os.path.dirname(os.path.abspath(__file__))


def load_source():
    """Read entry.txt next to this script; return its raw bytes."""
    path = os.path.join(here(), "entry.txt")
    try:
        with open(path, "rb") as stream:
            return stream.read()
    except OSError as exc:
        fail("cannot read %s: %s" % (path, exc))


def as_text(raw):
    """Decode raw bytes as UTF-8, failing on bad encoding."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("entry.txt is not valid UTF-8")


def validate_line(line):
    """Check the one-line gate: length 1-200, no newlines, no padding."""
    if "\r" in line or "\n" in line:
        fail("entry.txt must hold exactly one line, no line breaks")
    size = len(line)
    if size < MIN_CHARS:
        fail("entry.txt is empty")
    if size > MAX_CHARS:
        fail("entry is %d chars, limit is %d" % (size, MAX_CHARS))
    if line.strip() != line:
        fail("entry.txt must not start or end with whitespace")
    if not line.strip():
        fail("entry.txt must not be blank")
    if "\t" in line:
        fail("entry.txt must not contain tab characters")
    if "  " in line:
        fail("entry.txt must not contain double spaces")
    for ch in line:
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            fail("entry.txt must not contain control characters")


def target_dir():
    """Output folder from the environment, defaulting to /output."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"


def make_dir(path):
    """Create path (including parents) when missing."""
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        fail("cannot create output dir %s: %s" % (path, exc))


def save(path, raw):
    """Write raw bytes to path."""
    try:
        with open(path, "wb") as stream:
            stream.write(raw)
    except OSError as exc:
        fail("cannot write %s: %s" % (path, exc))


def sha(raw):
    """SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(raw).hexdigest()


def verify_written(path, expected_digest):
    """Re-read path and fail unless its digest equals expected_digest."""
    try:
        with open(path, "rb") as stream:
            written = stream.read()
    except OSError as exc:
        fail("cannot re-read %s: %s" % (path, exc))
    if sha(written) != expected_digest:
        fail("output differs from entry.txt (sha256 mismatch)")


def main():
    raw = load_source()
    line = as_text(raw)
    validate_line(line)

    folder = target_dir()
    make_dir(folder)
    dest = os.path.join(folder, "entry.txt")
    save(dest, raw)
    verify_written(dest, sha(raw))

    print("wrote %d bytes, %d chars -> %s" % (len(raw), len(line), dest))
    print("sha256: %s" % sha(raw))


if __name__ == "__main__":
    main()
