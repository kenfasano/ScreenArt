import pandas as pd
import re
import os

def parse_log_file(file_path):
    """Parses a single log file into a dictionary of metrics."""
    data = {}
    with open(file_path, 'r') as f:
        content = f.read()

    # Extract Global Stats (Total)
    global_match = re.search(r'Min:\s*([\d.]+)s\s*\|\s*Avg:\s*([\d.]+)s\s*\|\s*Max:\s*([\d.]+)s', content)
    if global_match:
        data['Total'] = [float(x) for x in global_match.groups()]

    # Extract Per-Generator Stats
    # Matches "Name: -> Min: Xms | Avg: Yms | Max: Zms"
    gen_matches = re.findall(r'([\w\s\d]+):\s*->\s*Min:\s*([\d.]+)ms\s*\|\s*Avg:\s*([\d.]+)ms\s*\|\s*Max:\s*([\d.]+)ms', content)
    for name, min_val, avg_val, max_val in gen_matches:
        data[name.strip()] = [float(min_val), float(avg_val), float(max_val)]
    
    return data

def merge_logs(file_list):
    # 1. Gather all unique generator names across all files
    all_generators = ['Total']
    parsed_files = []
    
    for file in file_list:
        parsed_data = parse_log_file(file)
        parsed_files.append(parsed_data)
        for gen in parsed_data.keys():
            if gen not in all_generators:
                all_generators.append(gen)

    # 2. Build the result table
    result_rows = []
    for gen in all_generators:
        row = {'Generator': gen}
        prev_avg = None
        
        for i, data in enumerate(parsed_files):
            suffix = f"_v{i}"
            # Get values or defaults if generator is missing in this file
            vals = data.get(gen, [None, None, None])
            curr_min, curr_avg, curr_max = vals
            
            row[f'Min{suffix}'] = curr_min
            row[f'Avg{suffix}'] = curr_avg
            row[f'Max{suffix}'] = curr_max
            
            # Calculate Avg Change % starting from the second file
            if i > 0:
                change = None
                if prev_avg and curr_avg:
                    # Formula: (prev_avg - current_avg) / prev_avg
                    change = (prev_avg - curr_avg) / prev_avg
                row[f'Avg_Change_Pct{suffix}'] = change
            
            # Update prev_avg for the next file iteration
            if curr_avg is not None:
                prev_avg = curr_avg
                
        result_rows.append(row)

    df = pd.DataFrame(result_rows)
    return df

# Usage
# Ensure your files are sorted by creation time
files = ['log_durations_no_opt.txt', 'log_durations_prune_logging.txt']
# files.sort(key=os.path.getmtime) # Uncomment to sort by disk save time

df_final = merge_logs(files)

# Formatting for display/Excel: Commas and 2 decimal places
pd.options.display.float_format = '{:,.2f}'.format
print(df_final)

# To export to CSV for Excel:
# df_final.to_csv('merged_durations.csv', index=False)
