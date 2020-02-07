

"""
Implements an SQL database writer and reader for storing CAN messages.
.. note:: The database schema is given in the documentation of the loggers.
"""

import time
import threading
import logging
import cantools
from influxdb import InfluxDBClient
from influxdb import exceptions as ifxexcept
import time
import traceback
from can.listener import BufferedReader
from can.message import Message
from can.io.generic import BaseIOHandler

log = logging.getLogger("can.io.influxdb")

class InfluxWriter(BaseIOHandler, BufferedReader):
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

    GET_MESSAGE_TIMEOUT = 1
    """Number of seconds to wait for messages from internal queue"""

    MAX_TIME_BETWEEN_WRITES = 5.0
    """Maximum number of seconds to wait between writes to the database"""

    MAX_BUFFER_SIZE_BEFORE_WRITES = 500
    """Maximum number of messages to buffer before writing to the database"""

    def __init__(self, hostname,\
                 measurement_name="test",\
                 database_file='Model3CAN.dbc',\
                 database='mycar',\
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
        self._database = database+str(time.time_ns())
        self._measurement_name = measurement_name
        self._user = user
        self._password = password
        self._influxdb_host = hostname
        self._stop_running_event = threading.Event()
        self._client = None
        self._db = cantools.database.load_file(database_file)
        self.num_frames = 0
        self.last_write = time.time()
        self._one_json = lambda message:{ "measurement": self._measurement_name, "tags": {"message": message}, "time": None, "fields": {}}        
        self._writer_thread = threading.Thread(target=self._influx_writer_thread)
        self._writer_thread.start()

    def _connect(self):
        """Creates a new databae or opens a connection to an existing one.
        .. note::
            You can't share sqlite3 connections between threads (by default)
            hence we setup the db here. It has the upside of running async.
        """
        log.debug("Creating sqlite database")
        while True:
            try:
                self._client = InfluxDBClient(self._hostname, 38086, self._user, self._password, self._database)
                self._client.create_database(self._database)
                break
            except:
                log.info("reconnecting in 10")
                time.sleep(10)
        print('connected to '+str(self._hostname))

    def _influx_writer_thread(self):
        self._connect()

        try:
            while True:
                messages = []  # reset buffer

                msg = self.get_message(self.GET_MESSAGE_TIMEOUT)
                #print(str(msg))
                while msg is not None:
                    # log.debug("SqliteWriter: buffering message")
                    try:
                        decoded = self._db.decode_message(msg.arbitration_id, msg.data)
                        process = True
                    except:
                        log.info("not found in db: "+str(msg.arbitration_id))
                        process = False
                        break
                    if process:
                        basemsg = self._db.get_message_by_frame_id(msg.arbitration_id)
                        json_message = self._one_json(basemsg.name)
                        json_message["time"] = int(msg.timestamp*1000)
                        for name in list(decoded):
                            #if len([basemsg.get_signal_by_name(name)._choices]) > 1:
                            #    decoded[name] = str(decoded[name])
                            if decoded[name] == 'SNA':
                                del decoded[name]
                        json_message["fields"].update(decoded)
                        messages.append(json_message)
                    if (
                        time.time() - self.last_write > self.MAX_TIME_BETWEEN_WRITES
                        or len(messages) > self.MAX_BUFFER_SIZE_BEFORE_WRITES
                    ):
                        break
                    else:
                        # just go on
                        msg = self.get_message(self.GET_MESSAGE_TIMEOUT)

                count = len(messages)
                if count > 0:
                    # log.debug("Writing %d frames to db", count)
                    try:
                        self._client.write_points(messages, time_precision='ms')
                    except ifxexcept.InfluxDBClientError as e:
                        #print(str(message))
                        #print(message.timestamp)
                        print(e.content)
                        print(e.code)
                        try:
                            if e.content.find('partial write') > 0:
                                print(e.content.split('\\\"')[1])
                            else:
                                print(str(messages))
                        except:
                                print(str(messages))
                        traceback.print_exc()
                    except ifxexcept.InfluxDBServerError:
                        self._client.close()
                        self._connect()

                    self.num_frames += count
                    self.last_write = time.time()
                    print('influx: '+str(time.time())+' wrote '+str(count))

                # check if we are still supposed to run and go back up if yes
                if self._stop_running_event.is_set():
                    break

        finally:
            self._client.close()
            log.info("Stopped influxdb writer after writing %d messages", self.num_frames)

    def stop(self):
        """Stops the reader an writes all remaining messages to the database. Thus, this
        might take a while and block.
        """
        BufferedReader.stop(self)
        self._stop_running_event.set()
        self._writer_thread.join()
        BaseIOHandler.stop(self)
