#!/usr/bin/env python3
"""ScreenArt importer — imports HeartedQueue files into Photos.app ScreenArt album.

Runs periodically via launchd (every 5 minutes by default).
Idempotent: tracks already-imported filenames in .imported so re-runs are safe.
"""
import logging
import subprocess
import sys
from pathlib import Path

from config import ALBUM_NAME, HEARTED_QUEUE, IMPORTED_LOG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def already_imported() -> set:
    if not IMPORTED_LOG.exists():
        return set()
    return set(
        line for line in IMPORTED_LOG.read_text().splitlines() if line.strip()
    )


def mark_imported(filename: str) -> None:
    IMPORTED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with IMPORTED_LOG.open("a") as f:
        f.write(filename + "\n")


def import_to_photos(path: Path) -> bool:
    """Import a single file into the ScreenArt album via osascript."""
    # Escape any embedded quotes in path before substituting into AppleScript
    posix_path = str(path).replace('"', '\\"')
    script = f'''
    tell application "Photos"
        if not (exists album "{ALBUM_NAME}") then
            make new album named "{ALBUM_NAME}"
        end if
        import {{POSIX file "{posix_path}"}} into album "{ALBUM_NAME}" skip check duplicates yes
    end tell
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(
            "osascript failed for %s: %s",
            path.name,
            result.stderr.strip(),
        )
        return False
    log.info("imported %s", path.name)
    if result.stdout.strip():
        log.debug("osascript stdout: %s", result.stdout.strip())
    return True


def main() -> int:
    log.info("=== importer run ===")

    if not HEARTED_QUEUE.exists():
        log.info("no queue dir, nothing to do")
        return 0

    files = sorted(p for p in HEARTED_QUEUE.iterdir() if p.is_file())
    if not files:
        log.info("queue empty")
        return 0

    log.info("found %d file(s) in queue", len(files))
    imported = already_imported()

    success_count = 0
    skip_count = 0
    fail_count = 0

    for path in files:
        if path.name in imported:
            log.info(
                "already imported %s, removing from queue", path.name
            )
            path.unlink()
            skip_count += 1
            continue

        if import_to_photos(path):
            mark_imported(path.name)
            path.unlink()
            success_count += 1
        else:
            # Leave it in queue; retry next cycle
            fail_count += 1

    log.info(
        "done: %d imported, %d skipped, %d failed",
        success_count, skip_count, fail_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
