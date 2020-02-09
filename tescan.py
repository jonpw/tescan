import can
import sys, getopt
from influx import InfluxWriter
from mqttlistener import MqttWriter
import time

candev='vcan0'
doprint=True
doupload=True
dolog=True
vehicle = 'maximus'

try:
    opts, args = getopt.getopt(sys.argv[1:],"thdlb:p")
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
        doprint=True
        dolog=False
        doupload=False
    elif opt in ("-d"):
        doprint=False
        doupload=True
        dolog=True
    elif opt in ("-t"):
        doprint=True
        doupload=True
        dolog=True        
        vehicle='maximustest'
    elif opt in ("-l"):
        doprint=False
        doupload=False
        dolog=True
print('Using bus '+candev)

bus = can.Bus(bustype='socketcan', channel=candev, bitrate=500000, listen_only=True)

hostname = '701.insi.dev'
user = 'maximus'
password = 'campari'
database_file='model3dbc/Model3CAN.dbc'
sqlitefile = '/var/lib/tescanlogs/canbus.'+str(time.time_ns())+'.sqlite'

if doprint:
    printer = can.Printer()
if doupload:
    influxwriter = InfluxWriter(hostname, database=vehicle, measurement_name=vehicle, user=user, password=password, database_file=database_file)
    mqttwriter = MqttWriter(hostname, vehicle=vehicle, user=user, password=password, database_file=database_file)
if dolog:
    sqlitewriter = can.SqliteWriter(sqlitefile, table_name=vehicle)

while True:
    message = bus.recv()
    if doprint:
        printer(message)
    if dolog:
        sqlitewriter(message)
    if doupload:
        influxwriter(message)
        mqttwriter(message)
