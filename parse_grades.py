#!/usr/bin/env python3
"""
Parse transformer log files and output grades.csv with columns:
  generator, grade, transformers

transformers format: "TransformerName(key=val,...) | ..." (sorted alphabetically)
"""

import re
import csv
from pathlib import Path

# Matches:  "SomeTransformer","key=val,key=val"
TRANSFORMER_RE = re.compile(r'\] - "([A-Za-z]+Transformer)","([^"]*)"')

# Matches:  [Grade: A] Saved to: /path/to/bubbles_8-A.jpeg
GRADE_SAVED_RE = re.compile(r'\[Grade:\s*([A-F])\].*Saved to:\s*(\S+)')

# Extracts generator name from filename like bubbles_8-A.jpeg -> bubbles
GENERATOR_RE = re.compile(r'^(.*?)(_\d+)?-[A-F]\.(jpeg|jpg|png)$', re.IGNORECASE)


def get_generator(saved_path: str) -> str:
    filename = Path(saved_path).name
    m = GENERATOR_RE.match(filename)
    if m:
        return m.group(1)
    return Path(saved_path).stem


def parse_log_file(filepath: Path) -> list[tuple[str, str, str]]:
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
                generator = get_generator(saved_path)
                transformer_str = ' | '.join(sorted(current))
                results.append((generator, grade, transformer_str))
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

    all_results.sort(key=lambda r: (r[0], r[1], r[2]))

    output_path = Path('~/Scripts/ScreenArt/logs/grades.csv').expanduser()
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(['generator', 'grade', 'transformers'])
        for row in all_results:
            writer.writerow(row)

    print(f"\nWrote {len(all_results)} rows to {output_path}")


if __name__ == '__main__':
    main()
