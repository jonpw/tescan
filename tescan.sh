#!/bin/bash

cd /var/lib/tescan
git reset --hard
git pull
git submodule update
chmod 777 tescan.sh
while [ 1 ]
do
	myssid=$(iwgetid -r)
	candev=can0
	if [ myssid == "Telstra565C60" ]
	then
		candev=vcan0
	elif [ myssid == "jnet" ]
	then
		candev=can0
	elif [ myssid == "" ]
	then
		sleep 10
		continue
	fi
	touch /tmp/tescan.start
	sudo ip link set down ${candev} &&
	sudo ip link set ${candev} type can bitrate 500000 listen-only on && \
	sudo ip link set up ${candev} && \
	touch /tmp/tescan.run &&
	python3 tescan.py -b ${candev}
	echo Restarting
	sleep 60
done