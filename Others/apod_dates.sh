#!/bin/zsh
awk '/(Got|No).*img/ {
    # Determine the prefix based on what is in the line
    if ($0 ~ /Got/) {
        status = "Got"
    } else if ($0 ~ /No/) {
        status = "No img"
    }

    # Extract the year
    if (match($0, /ap[0-9]{6}/)) {
        yy = substr($0, RSTART+2, 2);
        year = (yy > 90 ? "19" : "20") yy;
        print status " " year;
    } else {
        # Fallback just in case a "No img" line doesnt contain the URL
        print status " (No URL/Year found)";
    }
}' logs/* | sort -r | uniq -c | sort -r 
