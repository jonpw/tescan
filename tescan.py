import can
import sys, getopt
from influx import InfluxWriter
from mqttlistener import MqttWriter

candev='vcan0'
printonly=False
doprint=True

try:
    opts, args = getopt.getopt(sys.argv[1:],"hdb:p")
except getopt.GetoptError:
    print('tescan.py -b <can device>')
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print('tescan.py -b <can device>')
        sys.exit()
    elif opt in ("-b"):
        candev = arg
    elif opt in ("-p"):
        printonly=True
    elif opt in ("-d"):
        doprint=False
print('Using bus '+candev)

bus = can.Bus(bustype='socketcan', channel=candev, bitrate=500000, receive_own_messages=True, listen_only=True)

hostname = '701.insi.dev'
vehicle = 'maximus'
user = vehicle
password = 'campari'
database_file='model3dbc/Model3CAN.dbc'
sqlitefile = '/var/lib/tescan/canbus.sqlite'

if doprint:
    printer = can.Printer()
if not printonly:
    influxwriter = InfluxWriter(hostname, database=vehicle, measurement_name=vehicle, user=user, password=password, database_file=database_file)
    sqlitewriter = can.SqliteWriter(sqlitefile, table_name=vehicle)
    mqttwriter = MqttWriter(hostname, vehicle=vehicle, user=user, password=password, database_file=database_file)

while True:
    message = bus.recv()
    if doprint:
        printer(message)
    if not printonly:
        sqlitewriter(message)
        influxwriter(message)
        mqttwriter(message)