import can
import cantools
from influxdb import InfluxDBClient
import time
import random

bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)
db = cantools.database.load_file('Model3CAN.dbc')
messages = db.messages

while True:
	message = messages[random.randint(0,len(messages))]
	sigdata = {}
	for signal in message.signals:
		if signal.is_float:
			sigdata[signal.name] = random.randint(signal.minimum, signal.maximum)
		else:
			sigdata[signal.name] = random.randint(signal.minimum, signal.maximum)
	encoded = message.encode(sigdata)
	new_message = can.Message(arbitration_id=message.frame_id, data=encoded)
	bus.send(new_message)
	time.sleep(0.1)



