import requests
import sys
import json


class mqsecPepEventRule():
    def __init__(self, name, nameBis, priority, action, target, decision):
        self.name = name
        self.nameBis = nameBis
        self.priority = priority
        self.action = action
        self.target = target
        self.decision = decision

    def __str__(self):
        res = ('smd:' + self.name + '\n' +
               '\ta mqsec:pepEventRule ;\n' +
               '\trdfs:label \"' + self.nameBis+'\" ;\n' +
               '\tmqsec:order ' + str(self.priority) + ' ;\n')
        if (self.action and self.action != ''):
            res += '\tmqsec:condition-action \"' + self.action + '\" ;\n'
        if (self.target and self.target != ''):
            res += '\tmqsec:condition-target-pattern \"'
            res += self.target + '\" ;\n'
        res += '\tmqsec:decision mqsec:' + self.decision + '.\n\n'
        return res


class mqsecPepEvent():
    def __init__(self, timestamp, action, source,
                 target, message='', name='mes'):

        '''
        :param timestamp
        :param action: publish or subscribe
        :param source: id_ of the client
        :param target: topic
        :param message: payload
        :param name
        '''

        self.name = name
        self.timestamp = timestamp
        self.action = action
        self.source = source
        self.target = target
        self.message = message
        self.prefix = (
            "@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> . \n" +
            "@prefix smd:    <http://bruno.univ-tln.fr/smartdemo/1.0#> .\n" +
            "@prefix mqsec:  <http://bruno.univ-tln.fr/mqsec/1.0#> .\n\n")

    def __str__(self):
        res = (
            self.prefix +
            "smd:" + self.name + '\n' +
            "   a mqsec:pepEvent ; \n" +
            "   mqsec:timestamp \"" +
            self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") +
            "\"^^xsd:dateTime  ;\n" +
            "   mqsec:action    \"" + self.action + "\" ;\n" +
            "   mqsec:source    \"" + self.source + "\" ;\n" +
            "   mqsec:target    \"" + self.target + "\" ")
        if (self.target == "publish"):
            res += ";\n    mqsec:message   \"" + self.message + "\" .\n"
        else:
            res += ".\n"

        return res

    def __repr__(self):
        str(self)


class PolicyDecisionPoint():
    def __init__(self):
        self.url = "http://10.9.0.81:8180/mqsec/manager"

    def submit_event(self, mqsec_pep_event):
        payload = mqsec_pep_event.__str__()
        url = self.url + '/event'
        headers = {'Accept': 'application/json', 'Content-Type': 'text/turtle'}

        session = requests.Session()
        session.trust_env = False
        r = session.post(url, headers=headers, data=payload)

        j = json.loads(r.text)

        processing_time = j['metadata'][0][1]
        print(processing_time)

        graph = j['payload']['@graph']
        if 'object' in graph[0]:
            decision = graph[0]['object']
        elif 'object' in graph[1]:
            decision = graph[1]['object']
        else:
            return False

        print(decision)
        return decision == 'mqsec:allow'

    def submit_policy(self, policy):
        " :param : policy: file name "
        try:
            f = open(policy, "rb")
        except FileNotFoundError:
            print("Rule file don't exist, create one")
            sys.exit(1)
        session = requests.Session()
        session.trust_env = False
        file = {'file': f}
        r = session.post(self.url + "/policy", files=file)
        # print(r.text)
        return r


if(__name__ == '__main__'):
    policy_decision_point = PolicyDecisionPoint()
    r = policy_decision_point.submit_policy('policy.ttl')

    f = open('e1.ttl', "rb")
    session = requests.Session()
    session.trust_env = False
    file = {'file': f}
    url = "http://10.9.0.81:8180/mqsec/manager/event"
    headers = {'Accept': 'application/json'}
    r = session.post(url, headers=headers, files=file)
    print(r.text)
