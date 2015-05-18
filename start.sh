#!/bin/bash
set -e
cd /home/alfred/python-rtmbot/
source bin/activate
python rtmbot.py
deactivate
