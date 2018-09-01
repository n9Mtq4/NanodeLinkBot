#!/bin/bash

# if it stops, restart after 10 minutes
while true; do
python3 -u nanodelinkbot.py comments | ts '[%Y-%m-%d %H:%M:%S]' | tee -a comments.log
sleep 600
done
