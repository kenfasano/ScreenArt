import pandas as pd
import re
import os
import glob
import subprocess
from openpyxl.styles import Border, Side, Font # type: ignore


def parse_results_file(file_path: str) -> tuple[int | None, dict[str, int]]:
    """
    Accepts:
      "Wiki  ->  6112ms"   (results.txt style)
      "Wiki  ->  6112"     (stripped log style)
    Returns:
      total_seconds (int | None), generators (dict {name: int})
    """
    total_seconds: int | None = None
    generators: dict[str, int] = {}

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"  [skip] not found: {file_path}")
        return total_seconds, generators

    if not lines:
        return total_seconds, generators

    # Line 1: "26s@17:54 ✓"  or  "26"
    m = re.match(r'^(\d+)', lines[0].strip())
    if m:
        total_seconds = int(m.group(1))

    # Generator block: after first '---', up to second '---' or end of file
    separators = [i for i, l in enumerate(lines) if l.strip() == '---']
    if separators:
        block_start = separators[0] + 1
        block_end   = separators[1] if len(separators) >= 2 else len(lines)
        for line in lines[block_start:block_end]:
            m2 = re.match(r'^(\S+)\s*->\s*(\d+)(?:ms)?', line.strip())
            if m2:
                generators[m2.group(1)] = int(m2.group(2))

    return total_seconds, generators


def get_color(val: float, min_val: float, max_val: float) -> str:
    if pd.isna(val):
        return "000000"
    if val < 0:
        if min_val >= 0:
            return "000000"
        ratio = val / min_val
        v = int(128 * (1 - ratio))
        return f"{v:02X}{v:02X}{v:02X}"
    else:
        if max_val <= 0:
            return "8B0000"
        ratio = val / max_val
        r  = int(128 + (139 - 128) * ratio)
        gb = int(128 * (1 - ratio))
        return f"{r:02X}{gb:02X}{gb:02X}"


def create_spreadsheet() -> None:
    log_dir      = os.path.expanduser("~/Scripts/ScreenArt/logs/log_durations")
    results_path = os.path.expanduser("~/Scripts/ScreenArt/results.txt")
    os.makedirs(log_dir, exist_ok=True)

    # ── 1. Parse results.txt ──────────────────────────────────────────────
    total_new, gens_new = parse_results_file(results_path)
    if total_new is None and not gens_new:
        print(f"Error: could not parse {results_path}")
        return

    # ── 2. Prompt and write new log file ─────────────────────────────────
    raw = input("Enter output filename for this run (default: log_durations.txt): ").strip()
    if not raw:
        raw = "log_durations.txt"
    if not raw.endswith('.txt'):
        raw += '.txt'
    new_log_path = os.path.join(log_dir, raw)

    with open(new_log_path, 'w') as f:
        if total_new is not None:
            f.write(f"{total_new}\n")
        f.write("---\n")
        for name, ms in gens_new.items():
            f.write(f"{name:<27} ->  {ms}\n")
        f.write("---\n")
    print(f"Log file saved: {new_log_path}")

    # ── 3. Glob *.txt only, sort by filename ascending ───────────────────
    files = sorted(glob.glob(os.path.join(log_dir, "*.txt")))
    if not files:
        print("No .txt files found.")
        return

    # ── 4. Parse every file ───────────────────────────────────────────────
    version_names      = []
    total_seconds_list = []
    generator_data     = []
    all_generators     = []

    for fp in files:
        total, gens = parse_results_file(fp)
        if total is None and not gens:
            continue
        # Initial cap, underscores to spaces — e.g. "main_timing" -> "Main timing"
        stem = os.path.basename(fp).replace('.txt', '').replace('_', ' ').capitalize()
        version_names.append(stem)
        total_seconds_list.append(total)
        generator_data.append(gens)
        for g in gens:
            if g not in all_generators:
                all_generators.append(g)

    if not version_names:
        print("No parseable data found.")
        return

    all_generators = ['Total'] + all_generators

    # ── 5. Build DataFrame ────────────────────────────────────────────────
    final_rows = []
    for gen in all_generators:
        row = {'Generator': gen}
        prev_val = None
        for i, gens in enumerate(generator_data):
            vname = version_names[i]
            val   = total_seconds_list[i] if gen == 'Total' else gens.get(gen)
            row[vname] = val if val is not None else 0
            if i > 0:
                row[f'{vname} Change %'] = (prev_val - val) / prev_val if (prev_val and val) else 0.0
            if val:
                prev_val = val
        final_rows.append(row)

    df = pd.DataFrame(final_rows)

    # ── 6. Write Excel ────────────────────────────────────────────────────
    output_path = os.path.join(log_dir, "log_durations.xlsx")
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    thick  = Side(style='thick', color="000000")
    thin   = Side(style='thin',  color="000000")

    CHUNK = 4
    version_chunks    = [version_names[i:i+CHUNK] for i in range(0, len(version_names), CHUNK)]
    current_start_row = 0
    worksheet         = None

    for chunk in version_chunks:
        chunk_cols = ['Generator']
        for col in df.columns:
            if col == 'Generator':
                continue
            for v in chunk:
                if col == v or col.startswith(v + ' '):
                    chunk_cols.append(col)
                    break

        chunk_df = df[chunk_cols].copy()
        chunk_df.to_excel(writer, index=False, sheet_name='Sheet1',
                          startrow=current_start_row)

        if worksheet is None:
            worksheet = writer.sheets['Sheet1']

        r_start_xl = current_start_row + 1
        r_end_xl   = current_start_row + len(chunk_df) + 1

        sections = []
        for v in chunk:
            sec_cols = [i+1 for i, c in enumerate(chunk_df.columns) if c == v or c.startswith(v + ' ')]
            if sec_cols:
                sections.append(sec_cols)

        for sec in sections:
            min_col, max_col = sec[0], sec[-1]
            for r in range(r_start_xl, r_end_xl + 1):
                for c in sec:
                    cell = worksheet.cell(row=r, column=c)
                    cell.border = Border(
                        top    = thick if r == r_start_xl else thin,
                        bottom = thick if r == r_end_xl   else thin,
                        left   = thick if c == min_col    else thin,
                        right  = thick if c == max_col    else thin,
                    )

        for i, col_name in enumerate(chunk_df.columns):
            if col_name.endswith('Change %'):
                col_idx = i + 1
                min_val = chunk_df[col_name].min()
                max_val = chunk_df[col_name].max()
                for row_idx in range(r_start_xl + 1, r_end_xl + 1):
                    val  = chunk_df.iloc[row_idx - r_start_xl - 1][col_name]
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    cell.number_format = '0.00%'
                    cell.font = Font(color=get_color(val, min_val, max_val), bold=True)

        current_start_row += len(chunk_df) + 3

    # Auto-fit columns
    for col in worksheet.columns:
        max_length = max((len(str(cell.value)) for cell in col if cell.value), default=0)
        worksheet.column_dimensions[col[0].column_letter].width = min(max_length + 4, 30)

    writer.close()
    print(f"Spreadsheet saved: {output_path}")

    try:
        subprocess.run(['open', '-a', 'LibreOffice', output_path])
    except Exception as e:
        print(f"Failed to auto-open: {e}")


if __name__ == "__main__":
    create_spreadsheet()
