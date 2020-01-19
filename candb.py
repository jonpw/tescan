import can
import influx

bus = can.Bus(bustype='socketcan', channel='vcan0', bitrate=500000, receive_own_messages=True)

hostname = '701.insi.dev'
vehicle = 'maximus'
user = vehicle
password = 'campari'

listener = InfluxWriter(hostname, database=vehicle, measurement=vehicle, user=user, password=password)

while True:
        message = bus.recv()
        listener(message)