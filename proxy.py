#!C:\Users\rgallier\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Python 3.7
# -*-coding:Latin-1 -*
import socket
from threading import Thread
import sys
import mqttMessage
import mqsec
import ruleFile

LISTENING_PORT = 1885
MQTT_BROKER_PORT = 1884
ADDR_MQTT_BROKER = 'localhost'
max_conn = 100
buffer_size = 8192


class threadClientProxy(Thread):
    '''
    Thread that listen the message send by the client
    and send them back to the server

    :param connexion_client: Connexion with the client (open)
    :param addr_client: Adress of the client (ip, port)
    :param socket_server: Connexion with the server (open)
    :param client_id: Id du client MQTT


    '''
    def __init__(self, connexion_client, addr_client,
                 socket_server, client_id, pdp):
        Thread.__init__(self)
        self.connexion_client = connexion_client
        self.addr_client = addr_client
        self.socket_server = socket_server
        self.client_id = client_id
        self.pdp = pdp

    def run(self):
        try:
            while 1:
                data = self.connexion_client.recv(buffer_size)
                if (len(data) > 0):
                    m = mqttMessage.decode_message(data)

                    print(
                        'SOURCE: {0},  {1}'.format(
                            self.addr_client,
                            m
                        )
                    )

                    m_valid = True

                    if (m.message_type == mqttMessage.PUBLISH):
                        mqsec_message = mqsec.mqsecPepEvent(
                            m.time,
                            'publish',
                            self.client_id,
                            m.topic,
                            m.payload,
                            'mes')
                        m_valid = self.pdp.submit_event(mqsec_message)

                    elif (m.message_type == mqttMessage.SUBSCRIBE):
                        # A subscribe message is transmited only if all
                        # the topic of the topic_list are valid
                        for t in (m.topic_list):
                            mqsec_message = mqsec.mqsecModel(
                                m.time,
                                'subscribe',
                                self.client_id,
                                t['topic_filter'])
                            m_valid = m_valid and self.pdp.submit_event(
                                mqsec_message
                            )

                    if m_valid:
                        self.socket_server.send(data)
                    else:
                        # TODO
                        pass

                    if (m.message_type == mqttMessage.DISCONNECT):
                        break

            self.connexion_client.close()
            self.socket_server.close()

        except socket.error:
            self.connexion_client.close()
            self.socket_server.close()
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[*] User Requested an interupt")
            print("[*] Apllication Exiting ...")
            sys.exit()


class threadProxyServer(Thread):
    '''
        Thread that listen the message send by the client
        and send them back to the server

        :param connexion_client: Connexion with the client
        :param data: Initial message send by the client,
                     must be a CONNECT message
        :param addr_client: Adress of the client (ip, port)
    '''

    def __init__(self, connection_client, data, addr_client, pdp):
        Thread.__init__(self)

        mqtt_message = mqttMessage.decode_message(data)

        # TODO

        print('SOURCE: {0},  {1}'.format(addr_client,
                                         mqtt_message))
        if (mqtt_message.message_type != mqttMessage.CONNECT):
            sys.exit(1)
        self.connection_client = connection_client
        self.data = data
        self.addr_client = addr_client
        self.client_id = mqtt_message.client_id
        self.pdp = pdp

    def run(self):
        # Listen for message from the server and transmit them to the client
        try:
            # Open the socket with the server  #TODO metre a try juste pour ca 
            # et si ca marche c'est echec connexion broker
            socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_server.connect((ADDR_MQTT_BROKER, MQTT_BROKER_PORT))
            socket_server.send(self.data)

            # Create a thread_client
            thread_client = threadClientProxy(
                self.connection_client,
                self.addr_client,
                socket_server,
                self.client_id,
                self.pdp)
            thread_client.start()
            
            while 1:
                # Read reply or data to from end web server
                reply = socket_server.recv(buffer_size)

                if (len(reply) > 0):
                    m = mqttMessage.decode_message(reply)
                    print('&SOURCE: ({0},{1}),  {2}'
                          .format(
                              ADDR_MQTT_BROKER,
                              MQTT_BROKER_PORT,
                              m
                          )
                          )

                    m_valid = True

                    if (m.message_type == mqttMessage.PUBLISH):
                        mqsec_message = mqsec.mqsecModel(
                            m.time,
                            'publish',
                            'broker',
                            m.topic,
                            m.payload,
                            'mes')
                        m_valid = self.pdp.submit_event(mqsec_message)

                    # send reply back to the client
                    if m_valid:
                        self.connection_client.send(reply)

            socket_server.close()
            self.connection_client.close()

        except socket.error:
            socket_server.close()
            self.connection_client.close()
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[*] User Requested an interupt")
            print("[*] Apllication Exiting ...")
            sys.exit()


def start():
    """ Fonction that start the proxy and display the message received"""
    policy_decision_point = mqsec.PolicyDecisionPoint()
    r = policy_decision_point.submit_policy(ruleFile.FILE_NAME)
    
    try:
        # Start listening on the listening_port for client request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', listening_port))
        s.listen(max_conn)

        print("[*] Initializing Socket ...Done")
        print("[*] Sockets Bind Sucessfully ...")
        print("[*] Server Started Successfully [ %d]\n" % (listening_port))
    except Exception:
        print("[*] Unable To Initialize Socket")
        sys.exit(2)
    while 1:
        try:
            # Upon reception of a client request create a thread to handle it
            connexion_client, addr_client = s.accept()
            data = connexion_client.recv(buffer_size)

            thread_server = threadProxyServer(
                connexion_client,
                data,
                addr_client,
                policy_decision_point
            )
            thread_server.start()

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
