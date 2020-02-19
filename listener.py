from can.listener import BufferedReader
from can.message import Message
from can.io.generic import BaseIOHandler

class SmartBufferedReader(BufferedReader):
    MAX_BUFFER_SIZE = 65535
    def on_message_received(self, msg: Message):
        if self.is_stopped:
            raise RuntimeError("reader has already been stopped")
        else:
        	if self.buffer.qsize() < self.MAX_BUFFER_SIZE:
        		self.buffer.put(msg)
        	else:
        		pass

    def buffer_is_empty(self):
    	return self.buffer.empty()

    def buffer_is_full(self):
    	return (self.buffer.qsize() >= self.MAX_BUFFER_SIZE)

    def get_buffer_length(self):
    	return self.buffer.qsize()