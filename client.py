#from multiprocessing import Process, Queue
from threading import Thread, Event
from queue import Queue
import socket
import json

server = "localhost"
port = 5555
class client:

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.client.setblocking(False)
        self.client.settimeout(5.0)
        self.recv_buffer = ''
        self.data_queue = Queue()

        self._stopevent = Event()
        self.listen_process = Thread(target=self.wait_for_data)

    def connect(self):
        #self.write_message("Connecting...")
        try:
            self.client.connect((server, port))
            #self.write_message("Press P to Ready Up")
        except:
            #print("Timeout")
            return False
        self.listen_process.start()
        return True

    def send_and_receive(self, data):
        self.send_string(data)
        return self.wait_for_data()

    def send_string(self, data):
        self.client.send(data.encode())
    
    def wait_for_data(self):
        while not self._stopevent.isSet():
            try:
                payload = self.client.recv(1024).decode()
                #print(payload)
                payload = payload.split('\r\n')
                if len(payload) == 0:
                    continue
                payload[0] = self.recv_buffer + payload[0]
                self.recv_buffer = payload.pop()
            except socket.timeout:
                continue

            try:
                #print(payload)
                for data in payload:
                    data = json.loads(data)
                    if data:
                        print(data)
                        self.data_queue.put(data)
            except json.JSONDecodeError:
                pass

    def disconnect(self):
        self._stopevent.set()
        self.listen_process.join()
        self.client.close()

    