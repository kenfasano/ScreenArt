#!/bin/zsh
awk '
/Bubble count:/ {
    count = $NF
}
/Bubbles:/ {
    bubbles_time = $NF
    sub(/ms$/, "", bubbles_time) # Removes the "ms" from the end
    
    # Only print if we have a count from a previous line
    if (count != "") {
        print count","bubbles_time
        count = "" # Reset count to ensure we pair them correctly
    }
}' <logs/screenArt.log | sort -k1,1n -k2,2n >bubble_correlation.txt
