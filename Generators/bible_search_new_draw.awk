# Match any line containing our target metrics
/(font_search|image_new|draw_text)=/ {
    # Loop through all fields in the matched line
    for (i = 1; i <= NF; i++) {
        # Check if the field starts with one of our metrics
        if ($i ~ /^(font_search|image_new|draw_text)=/) {
            # Split the key=value pair (e.g., "font_search=108.2ms")
            split($i, kv, "=")
            metric = kv[1]
            val = kv[2]
            
            # Strip out everything except numbers and the decimal point
            gsub(/[^0-9.]/, "", val)
            val = val + 0 # Force conversion to a number
            
            # Update calculations
            count[metric]++
            sum[metric] += val
            
            # Initialize or update min/max
            if (count[metric] == 1) {
                min[metric] = val
                max[metric] = val
            } else {
                if (val < min[metric]) min[metric] = val
                if (val > max[metric]) max[metric] = val
            }
        }
    }
}

END {
    # Print the results in a formatted table
    printf "%-15s | %-10s | %-10s | %-10s\n", "Metric", "Min (ms)", "Avg (ms)", "Max (ms)"
    printf "----------------------------------------------------------\n"
    
    # Define the exact order requested
    split("font_search image_new draw_text", order, " ")
    for (i = 1; i <= 3; i++) {
        m = order[i]
        if (count[m] > 0) {
            avg = sum[m] / count[m]
            printf "%-15s | %10.2f | %10.2f | %10.2f\n", m, min[m], avg, max[m]
        }
    }
}
