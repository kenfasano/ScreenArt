"""
reformat_avg.py  —  converts a "three-value" log file to results.txt format,
taking the MIDDLE (avg) value from each row.

Input format:
    Total                      2s 30.12s 44s
    PeripheralDriftIllusion    37.06ms 45.39ms 66.32ms

Output format:
    30s@converted ✓
    ---
    PeripheralDriftIllusion    ->  45ms
    ---
"""
import re
import sys
import os


def parse_three_value_file(file_path: str) -> tuple[int | None, dict[str, int]]:
    total_seconds: int | None = None
    generators: dict[str, int] = {}

    with open(file_path, 'r') as f:
        lines = [l.rstrip() for l in f if l.strip()]

    for line in lines:
        # Split into name and the remaining tokens
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        # Find all numeric values (strip s/ms suffix)
        values = re.findall(r'[\d.]+(?:ms|s)?', ' '.join(parts[1:]))
        if len(values) < 3:
            continue
        # Middle value is avg
        mid_raw = values[1]
        num = float(re.sub(r'[^\d.]', '', mid_raw))
        ms_val = int(num) if mid_raw.endswith('ms') else int(num * 1000)

        if name == 'Total':
            total_seconds = int(num) if not mid_raw.endswith('ms') else int(num / 1000)
        else:
            generators[name] = ms_val

    return total_seconds, generators


def write_results_format(total: int | None, generators: dict[str, int], out_path: str) -> None:
    with open(out_path, 'w') as f:
        if total is not None:
            f.write(f"{total}s@converted ✓\n")
        f.write("---\n")
        for name, ms in generators.items():
            f.write(f"{name:<27} ->  {ms}ms\n")
        f.write("---\n")
    print(f"Written: {out_path}")


def main() -> None:
    if len(sys.argv) < 2:
        path = input("Input file path: ").strip()
    else:
        path = sys.argv[1]

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    total, generators = parse_three_value_file(path)
    base = os.path.splitext(path)[0]
    out_path = base + "_reformatted.txt"
    write_results_format(total, generators, out_path)


if __name__ == "__main__":
    main()
