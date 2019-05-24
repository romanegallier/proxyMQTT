import requests


class mqsecModel():

    def __init__(self, timestamp, action, source,
                 target, message='', name='mes'):

        self.name = name
        self.timestamp = timestamp
        self.action = action
        self.source = source
        self.target = target
        self.message = message

    def __str__(self):
        res = (
            "@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> . \n" +
            "@prefix smd:    <http://bruno.univ-tln.fr/smartdemo/1.0#> .\n" +
            "@prefix mqsec:  <http://bruno.univ-tln.fr/mqsec/1.0#> .\n\n" +
            "smd:" + self.name + '\n' +
            "   a mqsec:pepEvent ; \n" +
            "   mqsec:timestamp \"" +
            self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") +
            "\"^^xsd:dateTime  ;\n" +
            "   mqsec:action    \"" + self.action + "\" ;\n" +
            "   mqsec:source    \"" + self.source + "\" ;\n" +
            "   mqsec:target    \"" + self.target + "\" ;\n")
        if (self.target == "publish"):
            res += "    mqsec:message   \"" + self.message + "\" .\n"

        return res

    def check_event(self):
        payload = str(self)

        url = 'http://localhost:8180/mqsec/manager/event'
        headers = {'Accept': 'text/turtle', 'Content-Type': 'text/turtle'}
        # TODO changer en application/json
        # 'text/turtle'

        # r = requests.post(url, headers= headers, files=files)
        r = requests.post(url, headers=headers, data=payload)
        # TODO regarder si le message est valide
        return True
