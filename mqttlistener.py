

"""
Implements an SQL database writer and reader for storing CAN messages.
.. note:: The database schema is given in the documentation of the loggers.
"""

import time
import threading
import logging
import cantools
import time
import traceback
from can.listener import BufferedReader
from can.message import Message
from can.io.generic import BaseIOHandler
import paho.mqtt.client as mqtt
from listener import SmartBufferedReader

log = logging.getLogger("can.io.mqttdb")

class MqttWriter(BaseIOHandler, SmartBufferedReader):
    """Writes decoded CAN bus data to an InfluxDB server
    The database will be created when connecting
    Messages are internally buffered and written in a background
    thread. Ensures that all messages that are added before calling :meth:`~can.InfluxWriter.stop()`
    are actually written to the database after that call returns. Thus, calling
    :meth:`~can.InfluxWriter.stop()` may take a while.
    :attr str hostname: Server hostname
    :attr 
    :attr int num_frames: the number of frames actually written to the database, this
                          excludes messages that are still buffered
    :attr float last_write: the last time a message war actually written to the database,
                            as given by ``time.time()``
    .. note::
        When the listener's :meth:`~SqliteWriter.stop` method is called the
        thread writing to the database will continue to receive and internally
        buffer messages if they continue to arrive before the
        :attr:`~SqliteWriter.GET_MESSAGE_TIMEOUT`.
        If the :attr:`~SqliteWriter.GET_MESSAGE_TIMEOUT` expires before a message
        is received, the internal buffer is written out to the database file.
        However if the bus is still saturated with messages, the Listener
        will continue receiving until the :attr:`~can.SqliteWriter.MAX_TIME_BETWEEN_WRITES`
        timeout is reached or more than
        :attr:`~can.SqliteWriter.MAX_BUFFER_SIZE_BEFORE_WRITES` messages are buffered.
    .. note:: The database schema is given in the documentation of the loggers.
    """

    GET_MESSAGE_TIMEOUT = 0.25
    """Number of seconds to wait for messages from internal queue"""

    def __init__(self, hostname,\
                 database_file='model3dbc/Model3CAN.dbc',\
                 vehicle='mycar',\
                 user='mycar',\
                 password='mycar'):
        """
        :param file: a `str` or since Python 3.7 a path like object that points
                     to the database file to use
        :param str table_name: the name of the table to store messages in
        .. warning:: In contrary to all other readers/writers the Sqlite handlers
                     do not accept file-like objects as the `file` parameter.
        """
        super().__init__(file=None)
        self._hostname = hostname
        self._topic_prefix = vehicle
        self._client_id = user+vehicle
        self._user = user
        self._password = password
        self._stop_running_event = threading.Event()
        self._client = None
        self._db = cantools.database.load_file(database_file) 
        self.num_frames = 0                
        self._writer_thread = threading.Thread(target=self._mqtt_publisher_thread)
        self._writer_thread.start()

    def _connect(self):
        """Creates a new databae or opens a connection to an existing one.
        .. note::
            You can't share sqlite3 connections between threads (by default)
            hence we setup the db here. It has the upside of running async.
        """
        print("MQTTWriter connecting to "+self._hostname)
        while True:
                try:
                        self._client = mqtt.Client(client_id=self._client_id)
                        self._client.on_connect = self._on_connect
                        self._client.on_disconnect = self._on_disconnect
                        self._client.on_message = self._on_message
                        #self._client.on_log = lambda mqttc, obj, level, string: print(string)
                        #self._client.disable_logger()
                        self._client.username_pw_set(username=self._user, password=self._password)
                        self._client.reconnect_delay_set(min_delay=1, max_delay=120)
                        self._client.will_set('/'.join([self._topic_prefix, 'status']), payload='timeout', qos=0, retain=True)
                        self._client.connect(self._hostname, port=31883)
                        break
                except:
                        print("reconnecting in 10")
                        traceback.print_exc()
                        time.sleep(10)
        self._client.loop_start()                                                
        print('MQTTWriter connected to '+self._hostname)

    def _on_connect(self, client, userdata, flags, rc):
        print("MQTT Connection returned result: "+connack_string(rc))
        retval = self._client.publish('/'.join([self._topic_prefix, 'status']), payload='running', qos=0, retain=True)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("MQTT Unexpected disconnection.")

    def _on_message(self, client, userdata, message):
        print("Received message '" + str(message.payload) + "' on topic '"
            + message.topic + "' with QoS " + str(message.qos))

    def _mqtt_publisher_thread(self):

        self._connect()

        try:
            while True:
                msg = self.get_message(self.GET_MESSAGE_TIMEOUT)
                if msg is not None:
                    decoded = {}
                    try:
                        msgname = self._db.get_message_by_frame_id(msg.arbitration_id).name
                        decoded = self._db.decode_message(msg.arbitration_id, msg.data)
                    except:
                        #print("not found in db: "+str(msg.arbitration_id))
                        msgname = "ID"+hex(msg.arbitration_id)[2:].upper()
                        #print(str(msg))
                        decoded["unknown"]=','.join([str(x) for x in [msg.data.hex(), msg.is_extended_id, msg.is_error_frame, msg.is_remote_frame]])
                    for signal in decoded:
                        try:
                            retval = self._client.publish('/'.join([self._topic_prefix, msgname, signal]), payload=decoded[signal], qos=0, retain=False)
                            if (retval.rc == mqtt.MQTT_ERR_SUCCESS):
                                self.num_frames += 1
                            elif (retval.rc == mqtt.MQTT_ERR_NO_CONN):
                                self._connect() #message lost?
                            else:
                                print('MQTT pub failed with'+str(rc))
                        except:
                            print('MQTT exception in publish')
                            traceback.print_exc()
                # check if we are still supposed to run and go back up if yes
                if self._stop_running_event.is_set():
                    break
        except:
            print('MQTT exception')
            traceback.print_exc()
        finally:
            self._client.disconnect()
            log.info("MQTT Stopped mqtt publisher after writing %d messages", self.num_frames)

    def stop(self):
        """Stops the reader an writes all remaining messages to the database. Thus, this
        might take a while and block.
        """
        BufferedReader.stop(self)
        self._stop_running_event.set()
        self._writer_thread.join()
        BaseIOHandler.stop(self)
