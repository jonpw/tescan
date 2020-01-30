import can
from influx import InfluxWriter
from mqttlistener import MqttWriter

bus = can.Bus(bustype='socketcan', channel='vcan0', bitrate=500000, receive_own_messages=True, listen_only=True)

hostname = '701.insi.dev'
vehicle = 'maximus'
user = vehicle
password = 'campari'
database_file='model3dbc/Model3CAN.dbc'
sqlitefile = '/var/lib/tescan/canbus.sqlite'

influxwriter = InfluxWriter(hostname, database=vehicle, measurement_name=vehicle, user=user, password=password, database_file=database_file)
printer = can.Printer()
sqlitewriter = can.SqliteWriter(sqlitefile, table_name=vehicle)
mqttwriter = MqttWriter(hostname, vehicle=vehicle, user=user, password=password, database_file=database_file)

while True:
    message = bus.recv()
    #printer(message)
    #sqlitewriter(message)
    #influxwriter(message)
    mqttwriter(message)