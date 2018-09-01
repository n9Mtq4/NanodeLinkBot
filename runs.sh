#!/bin/bash

# if it stops, restart after 10 minutes
while true; do
python3 -u nanodelinkbot.py submissions | ts '[%Y-%m-%d %H:%M:%S]' | tee -a submissions.log
sleep 600
done
