import socket
import select
import json

server_addr = "localhost"
port = 5555

class Server:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connected_players = []
        try:
            self.server.bind((server_addr, port))
        except socket.error as e:
            str(e)
    
    def listening_for_players(self):
        self.server.listen()
        conn, addr = self.server.accept()
        conn.setblocking(False)
        print(addr, "Connected")
        self.connected_players.append(conn)
        response = {'msg': 'Please ready up', 'player': 0}
        self.send_json(conn, response)

    
    def wait_for_player_res(self, player_num):
        reply, _, _ = select.select([self.connected_players[player_num]],[],[])
        data = reply[0].recv(1024).decode()
        print(data)
        return data

    def send_json_to_all(self, data):
        print("Sending ", data, " to all")
        sent = [False] * len(self.connected_players)

        while not all(sent):
            _, readied, _ = select.select([],self.connected_players,[])
            for conn in readied:
                self.send_json(conn, data)
                num = self.connected_players.index(conn)
                sent[num] = True
        print("Sent to all!")

    
    def send_json_to_player(self, data, player_num):
        print("Sending ", data, " player ", player_num)
        sent = False

        while not sent:
            _, readied, _ = select.select([],[self.connected_players[player_num]],[])
            for conn in readied:
                self.send_json(conn, data)
                sent = True
        print("Sent to player ", player_num)
        

    def send_json(self, conn, data):
        json_data = json.dumps(data) + '\r\n' 
        conn.send(json_data.encode())

    
    def block_wait_player_ready(self):
        ready = [False] * len(self.connected_players)
        while not all(ready):
            replies, _, _ = select.select(self.connected_players,[],[])
            for conn in replies:
                data = conn.recv(1024).decode()
                print(data)
                if data == "ready":
                    num = self.connected_players.index(conn)
                    ready[num] = True