import paho.mqtt.client as mqtt  # import the client1
import time
from threading import Thread
from arbres import Arbre
from random import randint
import random
import datetime

BROKER_ADRESS = 'localhost'
BROKER_PORT = 1885
KEEP_ALIVE = 60


def on_message(client, userdata, message):
    m = message.payload.decode("utf-8")
    s2 = m[-26:]
    date_time_obj = datetime.datetime.strptime(s2, '%Y-%m-%d %H:%M:%S.%f')
    timestamp = datetime.datetime.now()
    c = timestamp - date_time_obj
    print("message received ", str(message.payload.decode("utf-8")))
    # print("message topic=",message.topic)
    # print("message qos=",message.qos)
    # print("message retain flag=",message.retain)
    # print(timestamp)
    print(c)


def publish(clientId, topic, payload, qos, stayAlive):
    client = mqtt.Client(clientId)
    client.connect(BROKER_ADRESS, BROKER_PORT, KEEP_ALIVE)
    client.publish(topic, payload, qos)
    time.sleep(stayAlive)
    client.loop_stop()


def subscribe(clientId, topic, qos, stayAlive):
    client = mqtt.Client(clientId)
    client.on_message = on_message
    client.connect(BROKER_ADRESS, BROKER_PORT, KEEP_ALIVE)
    print(clientId + ' subscribe on topic ' + topic)
    client.subscribe(topic, qos)
    time.sleep(stayAlive)
    client.loop_stop()
    print(clientId + ' fin_subscribe')


class subscribeThread (Thread):
    def __init__(self, clientId, topic, qos, stayAlive):
        Thread.__init__(self)
        self.clientId = clientId
        self.topic = topic
        self.qos = qos
        self.stayAlive = stayAlive

    def run(self):
        try:
            client = mqtt.Client(self.clientId)
            client.on_message = on_message
            client.connect(BROKER_ADRESS, BROKER_PORT, KEEP_ALIVE)
            client.loop_start()
            print(self.clientId + ' subscribe on topic ' + self.topic)
            client.subscribe(self.topic, self.qos)
            time.sleep(self.stayAlive)
            client.loop_stop()
            print(self.clientId + ' fin_subscribe')
        except BaseException as e:
            print("Error in subscribeThread:\n" + str(e))


class publishThread (Thread):
    def __init__(self, clientId, topic, payload, qos, stayAlive):
        Thread.__init__(self)
        self.clientId = clientId
        self.topic = topic
        self.qos = qos
        self.stayAlive = stayAlive
        self.payload = payload

    def run(self):
        try:
            client = mqtt.Client(self.clientId)
            client.on_message = on_message
            client.loop_start
            client.connect(BROKER_ADRESS, BROKER_PORT, KEEP_ALIVE)
            print(
                self.clientId +
                " publish on topic:" +
                self.topic + ' :' +
                self.payload
            )
            client.publish(self.topic, self.payload, self.qos)
            time.sleep(self.stayAlive)
            client.loop_stop()
        except BaseException as e:
            print(
                "Error in publishThread with topic " +
                self.topic + ":\n" + str(e))


class subscibersThread (Thread):
    def __init__(self, nb, topicList):
        Thread.__init__(self)
        self.nb = nb
        self.topicList = topicList

    def run(self):
        try:

            clientId = "Client_ID_sub"
            for i in range(1, self.nb):
                topic = getRandomTopic(self.topicList)
                qos = getRandomQOS()
                stayAlive = 10
                # print('s' + str(i))
                s = subscribeThread(clientId + str(i), topic, qos, stayAlive)
                s.start()
        except BaseException as e:
            print("Error in susbscribersThread:\n" + str(e))


class publishersThread (Thread):
    def __init__(self, nb, topicList):
        Thread.__init__(self)
        self.nb = nb
        self.topicList = topicList

    def run(self):
        try:

            for i in range(1, self.nb):
                topic = getRandomTopic(self.topicList)
                timestamp = datetime.datetime.now()
                qos = getRandomQOS()
                stayAlive = 10
                clientIdBase = "Client_ID_pub"
                clientId = clientIdBase + str(i)
                s = publishThread(
                    clientId=clientId,
                    topic=topic,
                    payload=clientId + ' ' + topic + ' ' + str(timestamp),
                    qos=qos,
                    stayAlive=stayAlive
                )
                s.start()
        except BaseException as e:
            print("Error in publishersThread:\n" + str(e))


def main():
    nb_publishers = 10
    nb_subscribers = 3
    a = generation_arbre(height_max=1, nb_max_child=2)
    print(a)
    topics_s = generate_topic_s(a)
    topics_p = generate_topic_p(a)
    print(topics_s)
    print(topics_p)
    nb_rule = 2

    createRulesFile(nb_rule, topics_s)

    s = subscibersThread(nb_subscribers, topics_s)
    s.start()
    p = publishersThread(nb_publishers, topics_p)
    p.start()
    s.join()
    p.join()


def generation_arbre(height=0, name='a', nb_max_child=5,
                     nb_min_child=0, height_max=5, height_min=0):
    if (height >= height_max):
        return Arbre('l_' + name)
    else:
        if (height < height_min and nb_min_child < 1):
            nb_child = randint(1, nb_max_child)
        else:
            nb_child = randint(nb_min_child, nb_max_child)

        if nb_child > 0:
            a = Arbre('n_' + name)
            for i in range(0, nb_child):
                a.ajoute(
                    generation_arbre(
                        height+1,
                        name + chr(ord('a')+i),
                        nb_max_child,
                        nb_min_child,
                        height_max,
                        height_min
                    )
                )
        else:
            a = Arbre('l_' + name)
    return a


def generate_topic_s(a, root='', wildcard=False, first=True):
    topic_list = []
    topic_list.append(root + a.racine)
    if root != '' and not wildcard and first:
        topic_list.append(root + '+')
        topic_list.append(root + '#')
    for f in a:
        topic_list += generate_topic_s(
            f,
            root + a.racine + '/',
            first=first
        )
        topic_list += generate_topic_s(
            f,
            root + '+/',
            wildcard or root == '',
            first=first
        )
        first = False
    return topic_list


def generate_topic_p(a, root=''):
    topic_list = []
    topic_list.append(root + a.racine)
    for f in a:
        topic_list += generate_topic_p(f, root + a.racine + '/')
    return topic_list


def getRandomTopic(topics):
    r = random.randint(0, len(topics)-1)
    return topics[r]


def getRandomQOS():
    return random.randint(0, 2)


def createRulesFile(nb_rule, topic):

    f = open("rule.ttl", "w")

    f.write(
        "@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n" +
        "@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .\n" +
        "@prefix sh:     <http://www.w3.org/ns/shacl#> .\n" +
        "@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .\n" +
        "@prefix mqsec:  <http://bruno.univ-tln.fr/mqsec/1.0#> .\n" +
        "@prefix smd:    <http://bruno.univ-tln.fr/smartdemo/1.0#> .\n" +
        "@prefix xacml:  <urn:oasis:names:tc:xacml:3.0:>\n\n\n"
    )

    f.write("#mqsec:policy {\n\n")

    # on default everythings is denied
    f.write("smd:rule1\n" +
            "\ta mqsec:pepEventRule ;\n" +
            "\trdfs:label \"Rule 1\" ;\n" +
            "\tmqsec:priority \"1\"^^xsd:int ;\n" +
            "\tmqsec:decision mqsec:deny .\n\n")

    for i in range(0, nb_rule):
        name = 'rule' + str(i+2)
        nameBis = "Rule " + str(i+2)
        priority = random.randint(1, 5)
        action = random.choice(['subscribe', 'publish', 'subscribe|publish'])
        target = getRandomTopic(topic)
        decision = random.choice(['allow', 'deny'])
        f.write(createRule(name, nameBis, priority, action, target, decision))

    f.write('## https://wiki.oasis-open.org/xacml/XACMLandRDF\n' +
            'smd:parameters\n\n' +
            '\t# denyOverrides:            urn:oasis:names:tc:xacml:3.0:' +
            'rule-combining-algorithm:deny-overrides\n' +
            '\t# permitOverrides:          urn:oasis:names:tc:xacml:3.0:' +
            'rule-combining-algorithm:permit-overrides\n' +
            '\t# firstApplicable:          urn:oasis:names:tc:xacml:1.0:' +
            'rule-combining-algorithm:first-applicable\n' +
            '\t# orderedDenyOverrides:     urn:oasis:names:tc:xacml:3.0:' +
            'rule-combining-algorithm:ordered-deny-overrides\n' +
            '\t# orderedPermitOverrides:   urn:oasis:names:tc:xacml:3.0:' +
            'rule-combining-algorithm:ordered-permit-overrides\n' +
            '\t# denyUnlessPermit:         urn:oasis:names:tc:xacml:3.0:' +
            'rule-combining-algorithm:deny-unless-permit\n' +
            '\t# permitUnlessDeny:         urn:oasis:names:tc:xacml:3.0:' +
            'rule-combining-algorithm:permit-unless-deny\n' +
            '\t# denyOverrides:            urn:oasis:names:tc:xacml:3.0:' +
            'policy-combining-algorithm:deny-overrides\n' +
            '\t# permitOverrides:          urn:oasis:names:tc:xacml:3.0:' +
            'policy-combining-algorithm:permit-overrides\n' +
            '\t# firstApplicable:          urn:oasis:names:tc:xacml:1.0:' +
            'policy-combining-algorithm:first-applicable\n' +
            '\t# onlyOneApplicable:        urn:oasis:names:tc:xacml:1.0:' +
            'policy-combining-algorithm:only-one-applicable\n' +
            '\t# orderedDenyOverrides:     urn:oasis:names:tc:xacml:3.0:' +
            'policy-combining-algorithm:ordered-deny-overrides\n' +
            '\t# orderedPermitOverrides:   urn:oasis:names:tc:xacml:3.0:' +
            'policy-combining-algorithm:ordered-permit-overrides\n' +
            '\t# denyUnlessPermit:         urn:oasis:names:tc:xacml:3.0:' +
            'policy-combining-algorithm:deny-unless-permit\n' +
            '\t# permitUnlessDeny:         urn:oasis:names:tc:xacml:3.0:' +
            'policy-combining-algorithm:permit-unless-deny\n' +
            '\t# onPermitApplySecond:      urn:oasis:names:tc:xacml:3.0:' +
            'policy-combining-algorithm:on-permit-apply-second\n\n' +
            '\tmqsec:conflict-resolution-policy <xacml:' +
            'rule-combining-algorithm:ordered-deny-overrides>\n' +
            '#}')
    f.close()


def createRule(name, nameBis, priority, action, target, decision):
    return ('smd:' + name + '\n' +
            '\ta mqsec:pepEventRule ;\n' +
            '\trdfs:label \"' + nameBis+'\" ;\n' +
            '\tmqsec:priority \"' + str(priority) + '\"^^xsd:int ;\n' +
            '\tmqsec:condition-action \"' + action + '\" ;\n' +
            '\tmqsec:condition-target \"' + target + '\" ;\n' +
            '\tmqsec:decision mqsec:' + decision + '.\n\n')


main()

# TODO generer les regles aleatoirement
