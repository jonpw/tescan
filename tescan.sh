#!/bin/bash

cd /var/lib/tescan
git pull
git submodule update
while [ 1 ]
do
	sudo ip link set can0 type can bitrate 500000 listen-only on && \
	sudo ip link set up can0 && \
	python3 tescan.py -b can0
	sleep 60
done