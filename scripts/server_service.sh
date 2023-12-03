#!/bin/sh

# set -e

echo "Starting server "

udisksctl mount --block-device /dev/sda

/home/jetson/repos/UAV/venv/bin/python /home/jetson/repos/UAV/examples/run_server.py