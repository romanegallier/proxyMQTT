#!C:\Users\rgallier\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Python 3.7
# -*-coding:Latin-1 -*
import socket
from threading import Thread
import os
import random
import sys
from threading import Thread
import time
import mqtt_message

LISTENING_PORT = 1883
MQTT_BROKER_PORT = 1884
ADDR_MQTT_BROKER = 'localhost'
max_conn = 100
buffer_size = 8192


class threadClientProxy(Thread):
    ''' 
        Thread that listen the message send by the client 
        and send them back to the server
        
        :param connexionClient: Connexion with the client (open)
        :param addrClient: Adress of the client (ip, port)
        :param socketServer: Connexion with the server (open)
        :param clientID: Id du client MQTT
        

    '''
    def __init__(self, connexionClient, addrClient, socketServer, clientID):
        Thread.__init__(self)
        self.connexionClient = connexionClient
        self.addrClient = addrClient
        self.socketServer = socketServer
        self.clientID = clientID

    def run(self):
        try:
            while 1:
                data = self.connexionClient.recv(buffer_size)
                if (len(data) > 0):
                    mqttMessage = mqtt_message.decodeMessage(data)
                    print('SOURCE: {0},  {1}'.format(self.addrClient,
                                                     mqttMessage))
                    self.socketServer.send(data)

                    if (mqttMessage.messageType == mqtt_message.DISCONNECT):
                        break
            self.connexionClient.close()
            self.socketServer.close()
        except socket.error:
            self.connexionClient.close()
            self.socketServer.close()
            sys.exit(1)


class threadProxyServer(Thread):
    ''' 
        Thread that listen the message send by the client 
        and send them back to the server
        
        :param connexionClient: Connexion with the client
        :param data: Initial message send by the client, 
                     must be a CONNECT message
        :param addrClient: Adress of the client (ip, port)
  
    '''
    def __init__(self, connectionClient, data, addrClient):
        Thread.__init__(self)

        mqttMessage = mqtt_message.decodeMessage(data)
        print('SOURCE: {0},  {1}'.format(addrClient,
                                         mqttMessage))
        if (mqttMessage.messageType != mqtt_message.CONNECT):
            sys.exit(1)
        self.connectionClient = connectionClient
        self.data = data
        self.addrClient = addrClient
        self.clientID = mqttMessage.clientID

    def run(self):
        # listen for message from the server and transmit them to the client
        try:
            socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socketServer.connect((ADDR_MQTT_BROKER, MQTT_BROKER_PORT))
            socketServer.send(self.data)

            threadClient = threadClientProxy(self.connectionClient,
                                             self.addrClient,
                                             socketServer,
                                             self.clientID)
            threadClient.start()
            while 1:
                # Read reply or data to from end web server
                reply = socketServer.recv(buffer_size)

                if (len(reply) > 0):
                    mqttMessage = mqtt_message.decodeMessage(reply)
                    print('SOURCE: ({0},{1}),  {2}'.format(ADDR_MQTT_BROKER,
                                                           MQTT_BROKER_PORT,
                                                           mqttMessage))
                    # send reply back to the client
                    self.connectionClient.send(reply)

            socketServer.close()
            self.connectionClient.close()

        except socket.error:
            socketServer.close()
            self.connectionClient.close()
            sys.exit(1)


def start():
    """ Fonction that start the proxy and display the message received"""
    try:
        # Start listening on the listening_port for client request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', listening_port))
        s.listen(max_conn)

        print("[*] Initializing Socket ...Done")
        print("[*] Sockets Bind Sucessfully ...")
        print("[*] Server Started Successfully [ %d]\n" % (listening_port))
    except Exception as e:
        print("[*] Unable To Initialize Socket")
        sys.exit(2)
    while 1:
        try:
            # Upon reception of a client request create a thread to handle it
            connexionClient, addrClient = s.accept()
            data = connexionClient.recv(buffer_size)

            threadServer = threadProxyServer(connexionClient, data, addrClient)
            threadServer.start()

        except KeyboardInterrupt:
            s.close()
            print("\n[*] Proxy Server Shutting Down ...")
            sys.exit(1)
    s.close()


try:
    # listening_port = int(input("[*]Enter Listening Port Number: "))
    listening_port = LISTENING_PORT
except KeyboardInterrupt:
    print("\n[*] User Requested an interupt")
    print("[*] Apllication Exiting ...")
    sys.exit()

start()
