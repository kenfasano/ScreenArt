#!/bin/zsh
awk -F'-' 'tolower($0) ~ /warning|error/ {print $NF}' logs/* | sort | uniq -c | sort -nr
