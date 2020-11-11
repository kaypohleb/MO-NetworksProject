import socket
import _pickle as pickle
import random
import string
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.settimeout(500)
        self.host = "192.168.0.169"
        self.port = 5000
        self.addr = (self.host, self.port)
        
    def connect(self,name):
        """
        connects to server and returns the id of the client that connected
        :param name: str
        :return: int reprsenting id
        """
        self.client.sendto(str.encode(name),self.addr)
        data, address = self.client.recvfrom(8)
        val = int(data.decode())
        return val # can be int because will be an int id

    def disconnect(self):
        """
        disconnects from the server
        :return: None
        """
        self.client.close()
    
    def receive(self,toRcv):
        data, address = self.client.recvfrom(32)
        

    def send(self, data, pick=False):
        """
        sends information to the server
        :param data: str
        :param pick: boolean if should pickle or not
        :return: str
        """
        
        try:
            print("[LOG] trying to send", data)
            if pick:
                self.client.sendto(pickle.dumps(data),self.addr)
            else:
                self.client.sendto(str.encode(data),self.addr)
            print("[LOG] sent data:", data)
            reply, address = self.client.recvfrom(2048*4)
            try:
                reply = pickle.loads(reply)
            except Exception as e:
                print(e)

            return reply
        except socket.error as e:
            print(e)