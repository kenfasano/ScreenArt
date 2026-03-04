# metrics.awk

# Match lines containing our target metrics
/load:|generate:|save:|Bible:/ {
    # The metric name is the second-to-last field (e.g., "load:")
    metric = $(NF-1)
    sub(/:/, "", metric)

    # The value is the last field (e.g., "0.28ms")
    val = $NF
    sub(/ms/, "", val)
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

END {
    # Print the results in a formatted table
    printf "%-10s | %-10s | %-10s | %-10s\n", "Metric", "Min (ms)", "Avg (ms)", "Max (ms)"
    printf "----------------------------------------------------\n"
    
    # Define the exact order requested
    split("load generate save Bible", order, " ")
    for (i = 1; i <= 4; i++) {
        m = order[i]
        if (count[m] > 0) {
            avg = sum[m] / count[m]
            printf "%-10s | %10.2f | %10.2f | %10.2f\n", m, min[m], avg, max[m]
        }
    }
}
