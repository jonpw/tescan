import can
import cantools
import paho.mqtt.client as mqtt
import time
import traceback

bus = can.Bus(bustype='socketcan', channel='vcan0', bitrate=500000, receive_own_messages=True)
db = cantools.database.load_file('Model3CAN.dbc')
vehicle = 'maximus'

while True:
        try:
        		client = mqtt.Client()
        		client.on_connect = on_connect
        		client.on_message = on_message
        		client.connect("701.insi.dev", 1883, 60)
        		client.loop_start()
                break
        except:
                time.sleep(10)


one_json = lambda message:{ "measurement": vehicle, "tags": {"message": message}, "time": int(time.time_ns()/1000), "fields": {}}
ilp = lambda message, time, signals:str(vehicle)+','+','.join([str(key)+'='+str(val) for ])
while True:
        message = bus.recv()
        decoded = db.decode_message(message.arbitration_id, message.data)
        json_message = one_json(db.get_message_by_frame_id(message.arbitration_id).name)
        json_message["time"] = int(message.timestamp*1000)
        json_message["fields"].update(decoded)

        json_body = [json_message,]
        #print(str(json_body))d
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
