import can
import time

logfile = 'Model3Log2019-10-02v10.asc'
first = True
bus = can.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)
timestart = time.time()

for msg in can.io.ASCReader(logfile):
	print(str(msg))
	if first:
		timelast = msg.timestamp
		first = False
	print(msg.timestamp)
	print(time.time())
	time.sleep(msg.timestamp-timelast)
	timelast = msg.timestamp
	bus.send(msg)
