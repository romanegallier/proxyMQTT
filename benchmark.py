import paho.mqtt.client as mqtt  # import the client1
import time
from threading import Thread
import sys
import random
import datetime
import requests
from topicTree import topicTree
import ruleFile

BROKER_ADRESS = 'localhost'
BROKER_PORT = 1885
KEEP_ALIVE = 60
NB_PUBLISHERS = 10
NB_SUSCRIBERS = 10


class subscribeThread (Thread):
    def __init__(self, clientId, topic, qos):
        Thread.__init__(self)
        self.clientId = clientId
        self.topic = topic
        self.qos = qos
        self.client = None
        self.keep_running = True

    def run(self):
        try:
            self.client = mqtt.Client(self.clientId)
            client = self.client
            client.on_message = self.on_message
            client.connect(BROKER_ADRESS, BROKER_PORT, KEEP_ALIVE)
            client.loop_start()
            client.subscribe(self.topic, self.qos)
            while self.keep_running:
                time.sleep(1)
        except BaseException as e:
            print("Error in subscribeThread:\n" + str(e))
            sys.exit()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.keep_running = False

    def on_message(self, client, userdata, message):
        decoded_message = message.payload.decode("utf-8")
        send_timestamp = datetime.datetime.strptime(
            decoded_message[-26:],
            '%Y-%m-%d %H:%M:%S.%f'
            )
        received_timestamp = datetime.datetime.now()
        delay = received_timestamp - send_timestamp
        print(delay)


class publishThread (Thread):
    def __init__(self, clientId, topic, payload, qos):
        Thread.__init__(self)
        self.clientId = clientId
        self.topic = topic
        self.qos = qos
        self.payload = payload
        self.keep_running = True

    def run(self):
        try:
            client = mqtt.Client(self.clientId)
            client.on_publish = self.on_publish
            client.loop_start
            client.connect(BROKER_ADRESS, BROKER_PORT, KEEP_ALIVE)
            client.publish(self.topic, self.payload, self.qos)
            client.loop_forever()
            while self.keep_running:
                time.sleep(1)
        except BaseException as e:
            print(
                "Error in publishThread with topic " +
                self.topic + ":\n" + str(e))
            sys.exit()

    def stop(self):
        self.keep_running = False

    def on_publish(self, client, userdata, message):
        client.disconnect()
        client.loop_stop()
        self.stop()


class subscibersThread (Thread):
    def __init__(self, nb, topicList):
        Thread.__init__(self)
        self.nb = nb
        self.topicList = topicList
        self.child_list = []

    def run(self):

        try:
            clientId = "Client_ID_sub"

            for i in range(0, self.nb):
                topic = getRandomTopic(self.topicList)
                qos = getRandomQOS()
                s = subscribeThread(clientId + str(i), topic, qos)
                s.start()
                self.child_list.append(s)

            for child in self.child_list:
                child.join()

        except BaseException as e:
            print("Error in susbscribersThread:\n" + str(e))
            sys.exit()

    def stop(self):
        for child in self.child_list:
            child.stop()


class publishersThread (Thread):
    def __init__(self, nb, topicList):
        Thread.__init__(self)
        self.nb = nb
        self.topicList = topicList

    def run(self):
        child_list = []
        clientIdBase = "Client_ID_pub"
        for i in range(0, self.nb):
            timestamp = datetime.datetime.now()
            clientId = clientIdBase + str(i)
            topic = getRandomTopic(self.topicList)
            p = publishThread(
                clientId=clientId,
                topic=topic,
                payload=clientId + ' ' + topic + ' ' + str(timestamp),
                qos=getRandomQOS()
            )

            p.start()
            child_list.append(p)

        for p in child_list:
            p.join()


def main(nb_subscribers=NB_SUSCRIBERS, nb_publishers=NB_PUBLISHERS):
    # Get the topic tree and the list of topic filter
    topic_tree = topicTree()
    try:
        topic_tree.read()
    except FileNotFoundError:
        topic_tree.generate_topic_tree(height_max=5, nb_max_child=5)
        topic_tree.write()

    topics_s = topic_tree.generate_topic_s()
    topics_p = topic_tree.generate_topic_p()

    # submit ruleFile to moteur
    try:
        f = open(ruleFile.FILE_NAME, 'rb')
    except FileNotFoundError:
        ruleFile.createRulesFile(topic=topics_s)
        f = open(ruleFile.FILE_NAME, 'rb')

    try:
        session = requests.Session()
        session.trust_env = False
        file = {'file': f}
        session.post("http://localhost:8180/mqsec/manager/policy", files=file)
    except Exception:
        print('Failed to post the policy')
        sys.exit(1)

    # Start the publishers and subscribers client
    s = subscibersThread(nb_subscribers, topics_s)
    s.start()
    p = publishersThread(nb_publishers, topics_p)
    p.start()

    p.join()
    time.sleep(2)
    s.stop()
    s.join()


def getRandomTopic(topics):
    r = random.randint(0, len(topics)-1)
    return topics[r]


def getRandomQOS():
    return random.randint(0, 2)


if(__name__ == '__main__'):
    if(len(sys.argv) > 2):
        main(sys.argv[1], sys.argv[2])
    else:
        main()
