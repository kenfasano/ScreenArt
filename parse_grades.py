#!/usr/bin/env python3
"""
Parse transformer log files and output grades.csv with columns:
  generator, grade, layout_mode, transformers

Filename formats supported:
  bubbles_8-A.jpeg          (no layout mode)
  lojong_0-A-tile.jpeg      (with layout mode)
  psalms_64-A-hero.jpeg     (with layout mode)
"""

import re
import csv
from pathlib import Path
from .source_type_map import SOURCE_TYPE_MAP

def infer_source_type(generator: str) -> str:
    g = generator.lower()
    for key, stype in SOURCE_TYPE_MAP.items():
        if key in g:
            return stype
    return "photo"

# Matches:  "SomeTransformer","key=val,key=val"
TRANSFORMER_RE = re.compile(r'\] - "([A-Za-z]+Transformer)","([^"]*)"')

# Matches:  [Grade: A] Saved to: /path/to/lojong_0-A-tile.jpeg
GRADE_SAVED_RE = re.compile(r'\[Grade:\s*([A-F])\].*Saved to:\s*(\S+)')

# Parses filename stem: group(1)=generator, group(3)=layout_mode or None
# Handles: name_N-GRADE, name_N-GRADE-mode, name-GRADE, name-GRADE-mode
FILENAME_RE = re.compile(
    r'^(.*?)(_\d+)?-[A-F](?:-([a-z]+))?\.(jpeg|jpg|png)$',
    re.IGNORECASE
)


def parse_filename(saved_path: str) -> tuple[str, str | None]:
    """Return (generator, layout_mode) from a graded filename."""
    filename = Path(saved_path).name
    m = FILENAME_RE.match(filename)
    if m:
        return m.group(1), m.group(3)   # group(3) is None if no mode tag
    return Path(saved_path).stem, None


def parse_log_file(filepath: Path) -> list[tuple]:
    results = []
    current: list[str] = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            t_match = TRANSFORMER_RE.search(line)
            if t_match:
                name = t_match.group(1)
                meta = t_match.group(2).strip()
                current.append(f"{name}({meta})" if meta else name)
                continue

            g_match = GRADE_SAVED_RE.search(line)
            if g_match:
                grade = g_match.group(1)
                saved_path = g_match.group(2)
                generator, layout_mode = parse_filename(saved_path)
                transformer_str = ' | '.join(sorted(current))
                results.append((
                    generator,
                    infer_source_type(generator),
                    grade,
                    layout_mode or '',
                    len(current),
                    transformer_str,
                ))
                current = []

    return results


def main() -> None:
    LOG_DIR = Path('~/Scripts/ScreenArt/logs').expanduser()
    log_files = sorted(LOG_DIR.glob("screenArt*.log"))

    all_results = []
    for lf in log_files:
        print(f"Parsing: {lf}")
        rows = parse_log_file(lf)
        print(f"  Found {len(rows)} entries")
        all_results.extend(rows)

    all_results.sort(key=lambda r: (r[0], r[2], r[5]))

    output_path = Path('~/Scripts/ScreenArt/logs/grades.csv').expanduser()
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(['generator', 'source_type', 'grade', 'layout_mode', 'transformer_count', 'transformers'])
        for row in all_results:
            writer.writerow(row)

    print(f"\nWrote {len(all_results)} rows to {output_path}")


if __name__ == '__main__':
    main()
