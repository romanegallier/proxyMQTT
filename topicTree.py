from arbres import Arbre
from random import randint
from ast import literal_eval


class topicTree():
    def __init__(self):
        self.arbre = None

    def generate_topic_tree(self, height=0, name='a', nb_max_child=5,
                            nb_min_child=0, height_max=5, height_min=0):
        self.arbre = self.__generate_topic_tree_rec(
            height,
            name,
            nb_max_child,
            nb_min_child,
            height_max,
            height_min
        )

    def __generate_topic_tree_rec(self, height=0, name='a', nb_max_child=5,
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
                        self.__generate_topic_tree_rec(
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

    def write(self, file_name='topicTree.txt'):
        f = open(file_name, "w")
        f.write(str(self))
        f.close()

    def __str__(self):
        return self.__topic_tree_to_string(self.arbre)

    def __topic_tree_to_string(self, a):
        res = '(\'' + a.racine + '\''
        for f in a:
            res += ',' + self.__topic_tree_to_string(f) 
        return res + ')'

    def read(self, file_name="topicTree.txt"):
        try:
            f = open(file_name, 'rt')
            self.arbre = Arbre(literal_eval(f.read()))
        except FileNotFoundError:
            raise FileNotFoundError

    def generate_topic_s(self):
        return self.__generate_topic_s_rec(self.arbre)

    def __generate_topic_s_rec(self, a, root='', wildcard=False, first=True):
        topic_list = []
        topic_list.append(root + a.racine)
        if root != '' and not wildcard and first:
            topic_list.append(root + '+')
            topic_list.append(root + '#')
        for f in a:
            topic_list += self.__generate_topic_s_rec(
                f,
                root + a.racine + '/',
                first=first
            )
            topic_list += self.__generate_topic_s_rec(
                f,
                root + '+/',
                wildcard or root == '',
                first=first
            )
            first = False
        return topic_list

    def generate_topic_p(self):
        return self.__generate_topic_p_rec(self.arbre)
    
    def __generate_topic_p_rec(self, a, root=''):
        topic_list = []
        topic_list.append(root + a.racine)
        for f in a:
            topic_list += self.__generate_topic_p_rec(f, root + a.racine + '/')
        return topic_list


if __name__ == '__main__':
    topic_tree = topicTree()
    topic_tree.generate_topic_tree(height_max=5, nb_max_child=5)
    topic_tree.write()