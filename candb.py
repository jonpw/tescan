import can
import cantools
from influxdb import InfluxDBClient
from influxdb import exceptions as ifxexcept
import time
import traceback

bus = can.Bus(bustype='socketcan', channel='vcan0', bitrate=500000, receive_own_messages=True)
db = cantools.database.load_file('Model3CAN.dbc')

while True:
        try:
                client = InfluxDBClient('701.insi.dev', 38086, 'maximus', 'campari', 'test')
                client.create_database('test')
                break
        except:
                time.sleep(10)

vehicle = 'maximus'

one_json = lambda message:{ "measurement": vehicle, "tags": {"message": message}, "time": int(time.time_ns()/1000), "fields": {}}

while True:
        message = bus.recv()
        decoded = db.decode_message(message.arbitration_id, message.data)
        json_message = one_json(db.get_message_by_frame_id(message.arbitration_id).name)
        json_message["time"] = int(message.timestamp*1000)
        json_message["fields"].update(decoded)
        json_body = [json_message,]
        #print(str(json_body))
        try:
                client.write_points(json_body)
        except ifxexcept.InfluxDBClientError:
                #print(str(message))
                #print(message.timestamp)
                print(str(json_body))
                traceback.print_exc()
        except ifxexcept.InfluxDBServerError:
                client.close()
                while True:
                        try:
                                client = InfluxDBClient('701.insi.dev', 38086, 'maximus', 'campari', 'test')
                                break
                        except:
                                print('Connection lost? Trying in 10s')
                                time.sleep(10)
