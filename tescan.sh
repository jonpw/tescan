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
	if [ "${myssid}" == "Telstra565C60" ]
	then
		candev=vcan0
		modprobe vcan
		sudo ip link add dev vcan0 type vcan && \
		sudo ip link set up ${candev}
		options="-t"
	elif [ "${myssid}" == "jnet" ]
	then
		candev=can0
		sudo ip link set down ${candev}
		sudo ip link set ${candev} type can bitrate 500000 listen-only on
	elif [ "${myssid}" == "" ]
	then
		sleep 10
		continue
	else
		echo ${myssid} unknown
		continue
	fi
	touch /tmp/tescan.run &&
	python3 tescan.py -b ${candev} ${options}
	echo Restarting
	sleep 60
done