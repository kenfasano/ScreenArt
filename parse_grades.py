#!/usr/bin/env python3
"""
Parse transformer log files and output grades.csv with columns:
  image_base, grade, transformers (alphabetically sorted, quoted)
"""

import re
import csv
from pathlib import Path

KNOWN_BASES = {
    'bible', 'bubbles', 'cubes', 'goes', 'hilbert',
    'kochSnowflake', 'kochSnowflake1', 'kochSnowflake2',
    'kochSnowflake3', 'kochSnowflake4', 'lojong', 'maps',
    'optical_illusion', 'peripheral_drift_illusion'
}

def get_base_name(saved_path):
    filename = Path(saved_path).stem          # e.g. "bubbles_8-F"
    base = BASENAME_SUFFIX_RE.sub('', Path(saved_path).name)  # strip _8-F.jpeg
    base = re.sub(r'_\d+$', '', base)        # strip any trailing _4 etc.
    return base.capitalize() if base in KNOWN_BASES else 'Photo'

# Patterns
TRANSFORMER_RE = re.compile(r'\] - ([A-Za-z]+Transformer)\s*$')
GRADE_SAVED_RE = re.compile(r'\[Grade:\s*([A-F])\].*Saved to:\s*(\S+)')
BASENAME_SUFFIX_RE = re.compile(r'_\d+-[ABCDEZ]\.(jpeg|jpg|png)$', re.IGNORECASE)

def parse_log_file(filepath):
    """Parse a single log file, returning a list of (base_name, grade, transformers) tuples."""
    results = []
    current_transformers = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Check for a transformer line
            t_match = TRANSFORMER_RE.search(line)
            if t_match:
                current_transformers.append(t_match.group(1))
                continue

            # Check for a grade+save line
            g_match = GRADE_SAVED_RE.search(line)
            if g_match:
                grade = g_match.group(1)
                saved_path = g_match.group(2)

                # Extract just the filename, then strip the suffix
                base_name = get_base_name(saved_path)

                # Sort transformers alphabetically
                sorted_transformers = sorted(current_transformers)
                transformer_str = ', '.join(sorted_transformers)

                results.append((base_name, grade, transformer_str))
                current_transformers = []  # reset for next group

    return results


def main():
    LOG_DIR = Path('~/Scripts/ScreenArt/logs').expanduser()
    log_files = sorted(LOG_DIR.glob("*.log"))

    all_results = []
    for lf in log_files:
        print(f"Parsing: {lf}")
        rows = parse_log_file(lf)
        print(f"  Found {len(rows)} entries")
        all_results.extend(rows)

    output_path = 'grades.csv'
    all_results.sort(key=lambda r: (r[0], r[1], r[2]))
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        for row in all_results:
            writer.writerow(row)

    print(f"\nWrote {len(all_results)} rows to {output_path}")


if __name__ == '__main__':
    main()
