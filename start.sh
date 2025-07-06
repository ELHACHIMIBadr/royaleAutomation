#!/bin/bash

# Lancer Flask avec Gunicorn (1 worker, port 5000)
gunicorn -w 1 -b 0.0.0.0:5000 main:flask_app
