#!/bin/bash

# Lancer Flask via gunicorn en arrière-plan
gunicorn -w 1 -b 0.0.0.0:5000 main:flask_app &

# Lancer le bot Telegram
python3 main.py
