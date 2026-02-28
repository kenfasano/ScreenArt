#!/bin/zsh

# 1. Prompt for the filename
# -r: raw input, -p: prompt text
print -n "Enter output filename (default: log_durations.txt): "
read -r log_durations_out
log_durations_out="logs/log_durations/${log_durations_out}"

# 2. Set default if the user just pressed Enter
if [[ -z "$log_durations_out" ]]; then
    log_durations_out="logs/log_durations/log_durations.txt"
fi

# 3. Run awk and pipe to tee
awk '
# --- Route 1: The "50s@12:31" logic ---
/@ [0-9:]* / || /@[0-9:]* / {
    split($(NF-1), parts, "@")
    seconds = parts[1]
    sub(/s$/, "", seconds)
    
    global_count++
    global_sum += seconds
    if (global_count == 1 || seconds < global_min) global_min = seconds
    if (global_count == 1 || seconds > global_max) global_max = seconds
}

# --- Route 2: The "Generator: 123.45ms" logic ---
/[0-9]*\.[0-9]*ms/ {
    n = split($0, parts, " - ")
    line_data = parts[n]
    
    if (match(line_data, /: /)) {
        gen_name = substr(line_data, 1, RSTART - 1)
        ms_val = substr(line_data, RSTART + 2)
        sub(/ms$/, "", ms_val)
        
        gen_count[gen_name]++
        gen_sum[gen_name] += ms_val
        if (gen_count[gen_name] == 1 || ms_val < gen_min[gen_name]) gen_min[gen_name] = ms_val
        if (gen_count[gen_name] == 1 || ms_val > gen_max[gen_name]) gen_max[gen_name] = ms_val
    }
}

END {
    print "--- Global Seconds Stats ---"
    if (global_count > 0) {
        printf "Min: %ds | Avg: %.2fs | Max: %ds\n", global_min, global_sum/global_count, global_max
    } else {
        print "No global matches found."
    }

    print "\n--- Per-Generator MS Stats ---"
    for (g in gen_count) {
        if (g != "") {
            printf "%-12s -> Min: %8.2fms | Avg: %8.2fms | Max: %8.2fms\n", \
                   g ":", gen_min[g], gen_sum[g]/gen_count[g], gen_max[g]
        }
    }
}' logs/screenArt.log | tee "$log_durations_out"

echo "\nResults saved to: $log_durations_out"
