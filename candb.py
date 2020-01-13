import can
import cantools
from influxdb import InfluxDBClient
import time

bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)
db = cantools.database.load_file('Model3CAN.dbc')
client = InfluxDBClient('701.insi.dev', 38086, 'maximus', 'campari', 'test')
client.create_database('test')
vehicle = 'maximus'

one_json = lambda message:{ "measurement": vehicle, "tags": {"message": message}, "time": int(time.time()), "fields": {}}

while True:
	message = bus.recv()
	decoded = db.decode_message(message.arbitration_id, message.data)
	json_message = one_json(message.name)
	json_message["fields"].update(decoded)
	json_body = [json_message,]
	client.write_points(json_body)




