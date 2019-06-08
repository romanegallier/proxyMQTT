import requests
from topicTree import topicTree
import ruleFile
import sys
# session = requests.Session()
# session.trust_env = False
# file = {'file': open("rule.ttl", "rb")}
# r = session.post("http://localhost:8180/mqsec/manager/policy", files=file)

# print(r.text)
NB = 50

topic_tree = topicTree()

for j in range(11, 21):
    print(j)
    for i in range(0, NB):
        topic_tree.generate_topic_tree(height_max=5, nb_max_child=5)
        topics_s = topic_tree.generate_topic_s()
        ruleFile.createRulesFile(topic=topics_s, nb_rule=(j * 100))
        f = open(ruleFile.FILE_NAME, 'rb')
        try:
            session = requests.Session()
            session.trust_env = False
            file = {'file': f}
            r = session.post(
                "http://localhost:8180/mqsec/manager/policy",
                files=file
            )
            print('*')
        except Exception:
            print('Failed to post the policy')
            sys.exit(1)
