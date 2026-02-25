#!/bin/zsh
awk '/@[0-9:]* / {
    # 1. Split the second-to-last field at the "@"
    split($(NF-1), parts, "@")
    seconds = parts[1]
    
    # 2. Strip the "s" from the end
    sub(/s$/, "", seconds)
    
    # 3. Accumulate the data
    count++
    sum += seconds
    
    # 4. Set min and max
    if (count == 1 || seconds < min) min = seconds
    if (count == 1 || seconds > max) max = seconds
}
END {
    # 5. Calculate average and print final stats
    if (count > 0) {
        printf "Min: %d | Avg: %.2f | Max: %d\n", min, sum/count, max
    } else {
        print "No matches found."
    }
}' logs/*.log
