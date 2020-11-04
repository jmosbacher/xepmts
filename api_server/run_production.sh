#!/bin/sh

gunicorn --log-level debug --workers 2 --name app -b 0.0.0.0:5000 --reload main:app