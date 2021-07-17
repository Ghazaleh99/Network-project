import threading
import socket
import argparse
import os
import hashlib

class Server(threading.Thread):
    """
    Supports management of server connections.
    Attributes:
        connections (list): A list of ServerSocket objects representing the active connections.
        host (str): The IP address of the listening socket.
        port (int): The port number of the listening socket.
    """
    def __init__(self, host, port):
        super().__init__()
        self.connections = []
        self.host = host
        self.port = port
    
    def run(self):
        """
        Creates the listening socket. The listening socket will use the SO_REUSEADDR option to
        allow binding to a previously-used socket address. This is a small-scale application which
        only supports one waiting connection at a time. 
        For each new connection, a ServerSocket thread is started to facilitate communications with
        that particular client. All ServerSocket objects are stored in the connections attribute.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.host, self.port))
        except socket.error as e:
            print(str(e))

        sock.listen(1)
        print('Listening at', sock.getsockname())

        while True:

            # Accept new connection
            sc, sockname = sock.accept()
            print('Accepted a new connection from {} to {}'.format(sc.getpeername(), sc.getsockname()))

            # Create new thread
            server_socket = ServerSocket(sc, sockname, self)
            
            # Start new thread
            server_socket.start()

            global ThreadCount
            ThreadCount = ThreadCount + 1
            print('Connection Request: ' + str(ThreadCount))
            
            # Add thread to active connections
            self.connections.append(server_socket)
            print('Ready to receive messages from', sc.getpeername())

    def broadcast(self, message, source):
        """
        Sends a message to all connected clients, except the source of the message.
        """
        for connection in self.connections:

            # Send to all connected clients except the source client
            if connection.sockname != source:
                connection.send(message)
                
    def unicast(self, message, source):
        """
        Sends a message to the connected clients.
        """
        for connection in self.connections:

            # Send to all connected clients except the source client
            if connection.sockname == source:
                connection.send(message)
    
    def remove_connection(self, connection):
        """
        Removes a ServerSocket thread from the connections attribute.
        Args:
            connection (ServerSocket): The ServerSocket thread to remove.
        """
        self.connections.remove(connection)


class ServerSocket(threading.Thread):
    """
    Supports communications with a connected client.
    Attributes:
        sc (socket.socket): The connected socket.
        sockname (tuple): The client socket address.
        server (Server): The parent thread.
    """
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server
    
    def openfile(self,flag):
        a = str(self.sockname)
        print('Loading Chat : ',self.sockname)
        try:
            fileClient = open(a+'.txt',"r", encoding='utf-8')
        except:
            print('Cant load Chat : ',self.sockname)
        Lines = fileClient.readlines()
        count = 0
        # Strips the newline character
        for line in Lines:
            count += 1
            message = "{}".format(line.strip()) +'\n'
            self.server.unicast(message, self.sockname)
        fileClient.close()
    
    def startchat(self,flag):
        if flag:
            self.openfile(flag)
        a = str(self.sockname)
        fileClient = open(a+'.txt',"w", encoding='utf-8')
        while True:
            message = self.sc.recv(2048).decode('ascii')
            # Client has closed the socket, exit the thread
            if message == 'QUIT':
                self.sc.close()
                server.remove_connection(self)
                break            
            else:
                fileClient.write(message)
                fileClient.write('\n')
                print(message)
                self.server.broadcast(message, self.sockname)
        fileClient.close()
    
    def run(self): #LOGIN - REGISTER
        self.sc.send(str.encode('ENTER USERNAME : ')) # Request Username
        self.sockname = self.sc.recv(2048)
        self.sc.send(str.encode('ENTER PASSWORD : ')) # Request Password
        password = self.sc.recv(2048)
        password = password.decode()
        self.sockname = self.sockname.decode()
        password=hashlib.sha256(str.encode(password)).hexdigest() # Password hash using SHA256
        # REGISTERATION PHASE   
        # If new user,  regiter in Hashtable Dictionary  
        if self.sockname not in HashTable:
            HashTable[self.sockname]=password
            self.sc.send(str.encode('Registeration Successful'))
            print('Registered : ',self.sockname)
            print("{:<8} {:<20}".format('USER','PASSWORD'))
            for k, v in HashTable.items():
                label, num = k,v
                print("{:<8} {:<20}".format(label, num))
                print("-------------------------------------------")
            self.startchat(0)
                
        else:
            # If already existing user, check if the entered password is correct
            if(HashTable[self.sockname] == password):
                self.sc.send(str.encode('Connection Successful')) # Response Code for Connected Client 
                print('Connected : ',self.sockname)
                self.startchat(1)
            else:
                self.sc.send(str.encode('Login Failed')) # Response code for login failed
                print('Connection denied : ',self.sockname)
                self.sc.close()
    

    
    def send(self, message):
        """
        Sends a message to the connected server.
        Args:
            message (str): The message to be sent.
        """
        self.sc.sendall(message.encode('ascii'))


def exit(server):
    """
    Allows the server administrator to shut down the server.
    Typing 'q' in the command line will close all active connections and exit the application.
    """
    while True:
        ipt = input('')
        if ipt == 'q':
            print('Closing all connections...')
            for connection in server.connections:
                connection.sc.close()
            print('Shutting down the server...')
            os._exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060,
                        help='TCP port (default 1060)')
    args = parser.parse_args()
    HashTable = {}
    global ThreadCount
    ThreadCount = 0
    # Create and start server thread
    server = Server(args.host, args.p)
    server.start()

    exit = threading.Thread(target = exit, args = (server,))
    exit.start()