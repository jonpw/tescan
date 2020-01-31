#!/bin/bash

cd /var/lib/tescan
git pull
git submodule update
sudo ip link set can0 type can bitrate 500000 listen-only yes && sudo ip link set up can0 && python3 tescan.py