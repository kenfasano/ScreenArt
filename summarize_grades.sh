#!/bin/zsh

cat logs/grades.csv | awk -F, '!/grade/ {gsub("\"", "", $2); print $2}' | sort | uniq -c
