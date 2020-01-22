import can
from influx import InfluxWriter

bus = can.Bus(bustype='socketcan', channel='vcan0', bitrate=500000, receive_own_messages=True)

hostname = '701.insi.dev'
vehicle = 'maximus'
user = vehicle
password = 'campari'
database_file='model3dbc/Model3CAN.dbc'
sqlitefile = '/var/lib/tescan/canbus.sqlite'

influxwriter = InfluxWriter(hostname, database=vehicle, measurement_name=vehicle, user=user, password=password, database_file=database_file)
printer = can.printer()
sqlitewriter = can.SqliteWriter(sqlitefile, table_name=vehicle)

while True:
        message = bus.recv()
        influxwriter(message)
        printer(message)
        sqlitewriter(message)
