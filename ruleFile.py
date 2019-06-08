from topicTree import topicTree
from mqsec import mqsecPepEventRule
import random
import sys

NB_RULE = 5
FILE_NAME = "rule.ttl"
PREFIX = (
    "@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n" +
    "@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .\n" +
    "@prefix sh:     <http://www.w3.org/ns/shacl#> .\n" +
    "@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .\n" +
    "@prefix mqsec:  <http://bruno.univ-tln.fr/mqsec/1.0#> .\n" +
    "@prefix smd:    <http://bruno.univ-tln.fr/smartdemo/1.0#> .\n" +
    "@prefix xacml:  <urn:oasis:names:tc:xacml:3.0:>\n\n\n"
)


def get_rules_file():
    try:
        f = open(FILE_NAME)
    except FileNotFoundError:
        print("Rule file don't exist, create one")
        sys.exit(1)
    return f


def createRulesFile(topic, nb_rule=NB_RULE):

    f = open(FILE_NAME, "w")

    f.write(PREFIX)

    f.write("#mqsec:policy {\n\n")

    # on default everythings is denied
    f.write("smd:rule1\n" +
            "\ta mqsec:pepEventRule ;\n" +
            "\trdfs:label \"Rule 1\" ;\n" +
            "\tmqsec:order 1 ;\n" +
            "\tmqsec:decision mqsec:deny .\n\n")

    # default_rule = createRule ('rule1', 'Rule 1', 1 , '', '', 'deny')

    for i in range(0, nb_rule):
        name = 'rule' + str(i+2)
        nameBis = "Rule " + str(i+2)
        priority = random.randint(1, 5)
        action = random.choice(['subscribe', 'publish', 'subscribe|publish'])
        target = getRandomTopic(topic)
        decision = random.choice(['allow', 'deny'])
        f.write(str(mqsecPepEventRule(name, nameBis, priority,
                                      action, target, decision)))

    f.write('# La politique de résolution de conflits peut être définie conformément à XACML\n' +
            '## https://wiki.oasis-open.org/xacml/XACMLandRDF\n' +
            'smd:conflict-resolution-policy\n' +
            '  a mqsec:pepEventRule ;\n' +
            '  rdfs:label "Conflict resolution policy" ;\n' +
            '  rdfs:comment \"La règle d\'ordre le plus élevé s\'applique, en cas d\'égalité deny est retenu.\"@fr;\n' +
            '  mqsec:conflict-resolution-policy <xacml:rule-combining-algorithm:ordered-deny-overrides> .\n')

    f.write('#}')
    f.close()


def getRandomTopic(topics):
    r = random.randint(0, len(topics)-1)
    return topics[r]


if __name__ == '__main__':

    try:
        topic_tree = topicTree()
        topic_tree.read()
        topics_s = topic_tree.generate_topic_s()
        createRulesFile(topics_s)
    except FileNotFoundError:
        print('Topic tree file do not exist, create one before')
