from Mastermind import *

ip = "localhost"
port = 6318

class Server(MastermindServerUDP):
    def callback_client_handle(self, connection_object, data):
        print("Echo server got: \""+str(data)+"\"")
        self.callback_client_send(connection_object, data)

if __name__ == "__main__":
    server = Server()
    server.connect(ip,port)
    try:
        server.accepting_allow_wait_forever()
    except:
        #Only way to break is with an exception
        pass
    server.accepting_disallow()
    server.disconnect_clients()
    server.disconnect()