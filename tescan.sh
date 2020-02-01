#!/bin/bash

cd /var/lib/tescan
git pull
git submodule update
chmod 777 tescan.sh
while [ 1 ]
do
	touch /tmp/tescan.start
	sudo ip link set can0 type can bitrate 500000 listen-only on && \
	sudo ip link set up can0 && \
	touch /tmp/tescan.run &&
	python3 tescan.py -b can0
	sleep 60
done