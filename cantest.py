import traceback
import can
import cantools
from influxdb import InfluxDBClient
import time
import random

bus = can.Bus(bustype='socketcan', channel='vcan0', bitrate=500000, receive_own_messages=True)
db = cantools.database.load_file('Model3CAN.dbc')
messages = db.messages

while True:
        time.sleep(0.1)
        message = random.choice(messages)
        #message = messages[0]
        sigdata = {}
        for signal in message.signals:
                #print(str(signal))
                try:
                        if signal.minimum == None:
                                min=0
                        else:
                                min=signal.minimum
                        if signal.maximum == None:
                                max=((2**signal.length)-1)*signal.scale
                        else:
                                max=signal.maximum
                        if signal.is_float:
                                sigdata[signal.name] = random.randint(int(min), int(max))
                        else:
                                sigdata[signal.name] = random.randint(int(min), int(max))
                except Exception:
                        print('Error creating :'+str(signal))
                        traceback.print_exc()
                        continue
        #print(str(sigdata))
        try:
                encoded = message.encode(sigdata)
        except:
                print('Error encoding :'+str(sigdata))
                print(message.signals)
                traceback.print_exc()
                continue
        new_message = can.Message(arbitration_id=message.frame_id, data=encoded)
        bus.send(new_message)
        #print(str(new_message))