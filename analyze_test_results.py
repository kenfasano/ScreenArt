import csv
import argparse
import sys
import os

def analyze_results(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: File '{csv_path}' not found.")
        sys.exit(1)

    data = []
    
    # Mapping for sorting: A is highest (4), F is lowest (0)
    grade_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}

    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            
            # specific check to ensure headers match expected ScreenArt format
            expected_headers = {"Transformer1", "Transformer2", "Grade", "Ratio", "Accepted", "Rejected"}
            if not expected_headers.issubset(set(reader.fieldnames or [])):
                print(f"Error: CSV headers do not match expected format: {expected_headers}")
                sys.exit(1)

            for row in reader:
                try:
                    # Parse Grade
                    raw_grade = row['Grade']
                    grade_val = grade_map.get(raw_grade, -1.0) # -1 for unknown grades
                    
                    item = {
                        'Transformer1': row['Transformer1'],
                        'Transformer2': row['Transformer2'],
                        'Grade': raw_grade,         # Keep original string for display
                        'GradeVal': grade_val,      # Use numeric value for sorting
                        'Ratio': float(row['Ratio']),
                        'Accepted': int(row['Accepted']),
                        'Rejected': int(row['Rejected'])
                    }
                    data.append(item)
                except ValueError:
                    # Skip rows with malformed numbers in other columns
                    continue

    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Sort by GradeVal (Descending), then by Ratio (Descending) as a tie-breaker
    sorted_data = sorted(data, key=lambda x: (x['GradeVal'], x['Ratio']), reverse=True)

    # Formatting for output
    header = f"{'Rank':<5} {'Transformer Pair':<55} {'Grade':<8} {'Ratio':<8} {'Acc/Rej'}"
    print("\n" + "="*95)
    print(f"ANALYSIS REPORT: {csv_path}")
    print(f"Total Combinations Tested: {len(sorted_data)}")
    print("="*95)
    print(header)
    print("-" * 95)

    for i, row in enumerate(sorted_data, 1):
        pair = f"{row['Transformer1']} + {row['Transformer2']}"
        # Truncate pair name if it's too long for the column
        if len(pair) > 52:
            pair = pair[:52] + "..."
            
        print(f"{i:<5} {pair:<55} {row['Grade']:<8} {row['Ratio']:<8.2f} {row['Accepted']}/{row['Rejected']}")
    
    print("-" * 95 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze ScreenArt test matrix CSV.")
    parser.add_argument('csv_file', nargs='?', default='ScreenArt/transformers.csv', 
                        help="Path to the CSV file (default: ScreenArt/transformers.csv)")
    
    args = parser.parse_args()
    analyze_results(args.csv_file)
