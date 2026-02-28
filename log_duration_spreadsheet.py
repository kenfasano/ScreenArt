import pandas as pd
import re
import os
import glob

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
    
    # Apply Number and Percentage Formatting
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if col.endswith('Change %'):
            # Convert decimal ratio to percentage string (e.g., 0.123 -> "12.30%")
            df[col] = (df[col] * 100).map('{:,.2f}%'.format)
        else:
            # Durations: ensure two decimal places (e.g., 5.0 -> 5.00)
            df[col] = df[col].round(2)
    
    # Resolve the home directory shortcut and ensure the directory exists - expanduser preserved
    output_path = os.path.expanduser('~/Scripts/ScreenArt/logs/log_durations/log_durations.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    # Console Preview formatting
    pd.options.display.float_format = '{:,.2f}'.format
    print(f"Processed files in order: {version_names}")
    print(df.to_string(index=False))
    print(f"\nSpreadsheet saved successfully to: {output_path}")

if __name__ == "__main__":
    create_spreadsheet()
