# cache_hit_miss.awk

# Track which cache event we just saw
/SIZE CACHE MISS/ { current_cache = "CACHE MISS" }
/SIZE CACHE HIT/  { current_cache = "CACHE HIT" }

# When we see 'lines=', process it for the current cache event
/lines=[0-9]+/ {
    if (current_cache != "") {
        # Extract just the number
        val = $0
        sub(/.*lines=/, "", val)
        sub(/[^0-9].*/, "", val)
        val = val + 0 # Force numeric type

        type = current_cache
        count[type]++
        sum[type] += val

        # Initialize or update min/max
        if (count[type] == 1) {
            min[type] = val
            max[type] = val
        } else {
            if (val < min[type]) min[type] = val
            if (val > max[type]) max[type] = val
        }
        
        # Reset to avoid incorrectly counting stray 'lines=' later
        current_cache = ""
    }
}

END {
    # Print the results in a formatted table
    printf "%-15s | %-10s | %-10s | %-10s | %-10s\n", "Metric", "Count", "Min Lines", "Avg Lines", "Max Lines"
    printf "----------------------------------------------------------------------\n"
    
    # Output HIT and MISS in a consistent order
    split("CACHE HIT,CACHE MISS", order, ",")
    for (i = 1; i <= 2; i++) {
        m = order[i]
        if (count[m] > 0) {
            avg = sum[m] / count[m]
            printf "%-15s | %-10d | %-10d | %-10.2f | %-10d\n", m, count[m], min[m], avg, max[m]
        } else {
            printf "%-15s | %-10d | %-10s | %-10s | %-10s\n", m, 0, "-", "-", "-"
        }
    }
}
