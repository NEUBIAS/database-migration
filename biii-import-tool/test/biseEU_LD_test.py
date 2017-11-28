import unittest
import json
import glob

from rdflib import Graph

from src.biseEU_importer import get_software_list
from src.biseEU_LD_export import get_node_as_linked_data
from src.biseEU_LD_export import import_to_graph
from src.biseEU_LD_export import rdfize

class UsersTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.connection = {
            'username': 'USERNAME',
            'password': 'PASSWORD',
            'url': 'http://biii.eu',
            'proxy': 'PROXY_URL'
        }

    @classmethod
    def tearDownClass(cls):
        print()

    # @unittest.skip('test_export_single_node')
    def test_export_single_node(self):
        graph = Graph()
        nodeID = 67
        # nodeID = 1116
        # nodeID = 31
        raw_jld = get_node_as_linked_data(nodeID, self.connection)
        import_to_graph(graph, raw_jld)
        print(str(graph.serialize(format='turtle').decode('utf-8')))

    @unittest.skip('test_live_bulk_export')
    def test_live_bulk_export(self):
        softwares = get_software_list(self.connection)
        graph = Graph()
        count = 0
        for s in softwares:
            print(str(count)+'. Exporting '+s['title']+': '+s['nid'])
            node_ld = get_node_as_linked_data(s['nid'], self.connection)
            import_to_graph(graph, node_ld)
            count += 1
            # if count > 100:
            #     break
        # print(str(graph.serialize(format='turtle').decode('utf-8')))
        graph.serialize(destination='neubias-dump-09192017.ttl', format='turtle')
        graph.serialize(destination='neubias-dump-09192017.json-ld', format='json-ld')

    @unittest.skip('test_bulk_export')
    def test_bulk_export(self):
        graph = Graph()
        count = 0
        l = glob.glob('/Users/gaignard-a/Desktop/dependentNodes/*.json')
        for f_name in l:
            with open(f_name, 'r') as data_file:
                print('RDFizing '+f_name)
                data_str = data_file.read()
            try:
                data = json.loads(data_str)
                node_ld = rdfize(data)
                import_to_graph(graph, node_ld)
                count += 1

                # if count > 100:
                #     break
            except json.JSONDecodeError:
                print("\t!! Error while parsing " + f_name + " !!")

        # print(str(graph.serialize(format='turtle').decode('utf-8')))
        graph.serialize(destination='local-dump.ttl', format='turtle')
        #graph.serialize(destination='neubias-dump.json-ld', format='json-ld')

if __name__ == '__main__':
    unittest.main()
