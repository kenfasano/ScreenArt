#!/bin/zsh

python3 ./parse_grades.py && ./summarize_grades.sh
sleep 10
./profile_sa.sh
