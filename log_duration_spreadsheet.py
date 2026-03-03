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
            content = f.read()
    except Exception:
        return data

    # 1. Parse Global Stats (Total) - handles potential newlines/wrapping
    global_pattern = r'Min:\s*([\d.]+)s.*?Avg:\s*([\d.]+)s.*?Max:\s*([\d.]+)s'
    global_match = re.search(global_pattern, content, re.DOTALL)
    if global_match:
        data['Total'] = [float(x) for x in global_match.groups()]

    # 2. Parse Generator Stats
    gen_pattern = r'([\w\s\d]+):\s*->\s*Min:\s*([\d.]+)ms.*?Avg:\s*([\d.]+)ms.*?Max:\s*([\d.]+)ms'
    gen_matches = re.findall(gen_pattern, content, re.DOTALL)

    for name, min_val, avg_val, max_val in gen_matches:
        data[name.strip()] = [float(min_val), float(avg_val), float(max_val)]
    
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
    # 1. Identify input files - expanduser preserved
    files = glob.glob(os.path.expanduser("~/Scripts/ScreenArt/logs/log_durations/log_durations_*.txt"))
    
    # 2. SORT BY LAST SAVED (MODIFICATION) TIME, ASCENDING (Oldest to Newest)
    files.sort(key=os.path.getmtime)
    
    if not files:
        print("Error: No log files found matching 'log_durations_*.txt'.")
        return

    all_generators = ['Total']
    parsed_results = []
    version_names = []
    
    # 3. Process each log file in chronological order
    for file in files:
        name = os.path.basename(file).replace('log_durations_', '').replace('.txt', '')
        display_name = name.replace('_', ' ').title()
        
        metrics = parse_log_file(file)
        if metrics:
            parsed_results.append(metrics)
            version_names.append(display_name)
            for gen in metrics.keys():
                if gen not in all_generators:
                    all_generators.append(gen)

    # 4. Build the comparison data
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

    # 5. Output to Excel
    df = pd.DataFrame(final_rows)
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        # Keep Change % as actual floats so color logic can utilize it
        if not col.endswith('Change %'):
            df[col] = df[col].round(2)
    
    output_path = os.path.expanduser('~/Scripts/ScreenArt/logs/log_durations/log_durations.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Use pandas ExcelWriter to hook into openpyxl
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    
    # Define border styles once
    thick = Side(style='thick', color="000000")
    thin = Side(style='thin', color="000000")
    
    # Chunk the versions into groups of 4
    chunk_size = 4
    version_chunks = [version_names[i:i + chunk_size] for i in range(0, len(version_names), chunk_size)]
    
    current_start_row = 0
    worksheet = None
    
    # Process each chunk of versions
    for chunk in version_chunks:
        # Select 'Generator' and columns belonging to the current version chunk
        chunk_cols = ['Generator']
        for col in df.columns:
            if col == 'Generator': 
                continue
            for v in chunk:
                if col.startswith(v + ' '):
                    chunk_cols.append(col)
                    break
                    
        chunk_df = df[chunk_cols].copy()
        
        # Write the chunk to the spreadsheet
        chunk_df.to_excel(writer, index=False, sheet_name='Sheet1', startrow=current_start_row)
        
        if worksheet is None:
            worksheet = writer.sheets['Sheet1']
            
        r_start_xl = current_start_row + 1
        r_end_xl = current_start_row + len(chunk_df) + 1
        
        # Identify column groupings (sections) for this chunk to box them
        sections = []
        for v in chunk:
            sec_cols = []
            for i, col in enumerate(chunk_df.columns):
                if col.startswith(v + ' '):
                    sec_cols.append(i + 1) # 1-based indexing for openpyxl
            if sec_cols:
                sections.append(sec_cols)
                
        # Apply thick box around each section within this chunk
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
                    
        # Format 'Change %' columns and inject numeric text colors for this chunk
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
                    
        # Offset the next chunk by the length of the current dataframe + a spacing gap (e.g., 2 blank rows)
        current_start_row += len(chunk_df) + 3

    writer.close()
    
    # Console Preview formatting
    df_preview = df.copy()
    for col in numeric_cols:
        if col.endswith('Change %'):
            df_preview[col] = (df_preview[col] * 100).map('{:,.2f}%'.format)
            
    pd.options.display.float_format = '{:,.2f}'.format
    print(f"Processed files in order: {version_names}")
    print(df_preview.to_string(index=False))
    print(f"\nSpreadsheet saved successfully to: {output_path}")

    try:
        print("Launching LibreOffice...")
        # The 'open -a' command is specific to macOS for opening files in a specific app
        subprocess.run(['open', '-a', 'LibreOffice', output_path])
    except Exception as e:
        print(f"Failed to auto-open LibreOffice: {e}")

if __name__ == "__main__":
    create_spreadsheet()
