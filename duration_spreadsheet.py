import pandas as pd
import re
import os
import glob
import subprocess
from openpyxl.styles import Border, Side, Font

def parse_log_file(file_path):
    """Parses a single log file into a dictionary of metrics."""
    data = {}
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception:
        return data

    for line in lines:
        line = line.strip()
        if not line: 
            continue

        parts = line.split()
        if not parts: 
            continue

        name = parts[0].replace(':', '')
        
        nums = []
        for part in parts[1:]:
            clean_num = re.sub(r'[^\d.]', '', part)
            if clean_num and clean_num != '.':
                nums.append(float(clean_num))

        if len(nums) >= 3:
            data[name] = nums[:3]
    
    return data

def get_color(val, min_val, max_val):
    """Interpolates font color between Black, Gray, and Deep Red"""
    if pd.isna(val): return "000000"
    if val < 0:
        if min_val >= 0: return "000000"
        ratio = val / min_val
        val_rgb = int(128 * (1 - ratio))
        return f"{val_rgb:02X}{val_rgb:02X}{val_rgb:02X}"
    else:
        if max_val <= 0: return "8B0000"
        ratio = val / max_val
        r = int(128 + (139 - 128) * ratio)
        gb = int(128 * (1 - ratio))
        return f"{r:02X}{gb:02X}{gb:02X}"

def create_spreadsheet():
    # 1. Identify input files
    files = glob.glob(os.path.expanduser("~/Scripts/ScreenArt/logs/log_durations/*.txt"))
    files.sort(key=os.path.getmtime)
    
    if not files:
        print("Error: No log files found matching 'log_durations_*.txt'.")
        return

    all_generators = ['Total']
    parsed_results = []
    version_names = []
    
    for file in files:
        name = os.path.basename(file).replace('.txt', '')
        display_name = name.replace('_', ' ').title()
        
        metrics = parse_log_file(file)
        if metrics:
            parsed_results.append(metrics)
            version_names.append(display_name)
            for gen in metrics.keys():
                if gen not in all_generators:
                    all_generators.append(gen)

    final_rows = []
    for gen in all_generators:
        row = {'Generator': gen}
        prev_avg = None
        
        for i, metrics in enumerate(parsed_results):
            col_prefix = version_names[i]
            m_min, m_avg, m_max = metrics.get(gen, [0.0, 0.0, 0.0])
            
            row[f'{col_prefix} Min'] = m_min
            row[f'{col_prefix} Avg'] = m_avg
            row[f'{col_prefix} Max'] = m_max
            
            if i > 0:
                change = 0.0
                if prev_avg and m_avg:
                    change = (prev_avg - m_avg) / prev_avg
                row[f'{col_prefix} Change %'] = change
            
            if m_avg > 0:
                prev_avg = m_avg
                
        final_rows.append(row)

    df = pd.DataFrame(final_rows)
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if not col.endswith('Change %'):
            df[col] = df[col].round(2)
    
    output_path = os.path.expanduser('~/Scripts/ScreenArt/logs/log_durations/log_durations.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    thick = Side(style='thick', color="000000")
    thin = Side(style='thin', color="000000")
    
    chunk_size = 4
    version_chunks = [version_names[i:i + chunk_size] for i in range(0, len(version_names), chunk_size)]
    current_start_row = 0
    worksheet = None
    
    for chunk in version_chunks:
        chunk_cols = ['Generator']
        for col in df.columns:
            if col == 'Generator': continue
            for v in chunk:
                if col.startswith(v + ' '):
                    chunk_cols.append(col)
                    break
                    
        chunk_df = df[chunk_cols].copy()
        chunk_df.to_excel(writer, index=False, sheet_name='Sheet1', startrow=current_start_row)
        
        if worksheet is None:
            worksheet = writer.sheets['Sheet1']
            
        r_start_xl = current_start_row + 1
        r_end_xl = current_start_row + len(chunk_df) + 1
        
        sections = []
        for v in chunk:
            sec_cols = []
            for i, col in enumerate(chunk_df.columns):
                if col.startswith(v + ' '):
                    sec_cols.append(i + 1)
            if sec_cols:
                sections.append(sec_cols)
                
        for sec in sections:
            min_col = sec[0]
            max_col = sec[-1]
            for r in range(r_start_xl, r_end_xl + 1):
                for c in sec:
                    cell = worksheet.cell(row=r, column=c)
                    border_kwargs = {
                        'top': thick if r == r_start_xl else thin,
                        'bottom': thick if r == r_end_xl else thin,
                        'left': thick if c == min_col else thin,
                        'right': thick if c == max_col else thin
                    }
                    cell.border = Border(**border_kwargs)
                    
        for i, col_name in enumerate(chunk_df.columns):
            if col_name.endswith('Change %'):
                col_idx = i + 1
                min_val = chunk_df[col_name].min()
                max_val = chunk_df[col_name].max()
                
                for row_idx in range(r_start_xl + 1, r_end_xl + 1):
                    val = chunk_df.iloc[row_idx - r_start_xl - 1][col_name]
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    cell.number_format = '0.00%'
                    hex_color = get_color(val, min_val, max_val)
                    cell.font = Font(color=hex_color, bold=True)
                    
        current_start_row += len(chunk_df) + 3

    # --- AUTO-FIT COLUMNS ---
    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter # Get the column name
        for cell in col:
            try:
                if cell.value:
                    # Calculate length of content (plus a small buffer)
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
            except:
                pass
        # Set a reasonable max width so it doesn't get absurdly wide
        adjusted_width = min(max_length + 4, 30)
        worksheet.column_dimensions[column].width = adjusted_width

    writer.close()
    print(f"Spreadsheet saved and formatted: {output_path}")

    try:
        subprocess.run(['open', '-a', 'LibreOffice', output_path])
    except Exception as e:
        print(f"Failed to auto-open: {e}")

if __name__ == "__main__":
    create_spreadsheet()
