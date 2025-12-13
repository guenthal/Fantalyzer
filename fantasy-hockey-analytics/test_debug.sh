#!/bin/bash
echo "n4r3jsf" | ./venv/bin/python main.py > debug_run.txt 2>&1
echo "Debug output written to debug_run.txt"
cat debug_run.txt | grep -A 20 "EXTRACTING STATS" | head -50
