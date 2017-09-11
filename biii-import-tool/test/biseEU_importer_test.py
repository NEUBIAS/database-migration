import unittest
import json
import glob

from src.biseEU_importer import get_web_service
from src.biseEU_importer import import_entry
from src.biseEU_importer import import_directory
from src.biseEU_importer import get_software_list
from src.biseEU_importer import get_software_node_id
from src.biseEU_importer import update_dependencies_in_directory


class ImportTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # cls.connection = {
        #     'username': 'migration',
        #     'password': 'Mimimig2020',
        #     'url': 'http://dev-bise2.pantheonsite.io',
        #     'proxy': 'http://cache.ha.univ-nantes.fr:3128'
        # }
        cls.connection = {
            'username': 'migration',
            'password': 'Mimimig2020',
            'url': 'http://dev-bise2.pantheonsite.io'
        }
        cls.jsonFile = "./data/dump/nodes_software/node2098.json"
        cls.jsonDir = "./data/dump/nodes_software"

    @classmethod
    def tearDownClass(cls):
        print()

    @unittest.skip("rest_api_is_alive")
    def test_biseEU_alive(self):
        c = self.connection
        http = get_web_service(c)
        req = http.request('GET', c["url"] + '/node/52?_format=json')
        data = json.loads(req.data.decode('utf-8'))
        # print(json.dumps(data, indent=4, sort_keys=True))
        self.assertEquals("SOAX", data["title"][0]["value"])
        self.assertEquals("Ting Xu ", data["field_has_author"][0]["value"])

    @unittest.skip("single import")
    def test_biseEU_single_import(self):
        c = self.connection
        import_entry(self.jsonFile, c)

    @unittest.skip("bulk import")
    def test_biseEU_bulk_import(self):
        c = self.connection
        import_directory(self.jsonDir, c)

    @unittest.skip("json validation check")
    def test_json_validity(self):
        l = glob.glob(self.jsonDir + "/*.json")
        for f_name in l:
            with open(f_name, 'r') as data_file:
                print(f_name)
                data_str = data_file.read()
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                print("\t!! Error while parsing "+f_name+" !!")

    @unittest.skip("get softwares from Drupal")
    def test_get_soft_list(self):
        c = self.connection
        data = get_software_list(c)
        print(json.dumps(data, indent=4, sort_keys=True))

    @unittest.skip("get software ID from title")
    def test_get_id(self):
        c = self.connection
        id = get_software_node_id(c,'ImarisAnnotate')
        print('ImarisAnnotate --> '+str(id))
        self.assertEqual(id, '196')

    @unittest.skip("update dependencies from JSON dir")
    def test_update_dependencies_in_directory(self):
        c = self.connection
        # map = build_title_old_new_id_from_directory(self.jsonDir)
        update_dependencies_in_directory('/Users/gaignard-a/Desktop/data-florian/**/*.json', c)
        # print(json.dumps(map, indent=4))

    @unittest.skip("show duplicate IDs")
    def test_show_duplicate_titles(self):
        old_entries = []
        path_str = '/Users/gaignard-a/Desktop/data-florian/**/*.json'
        f_list = glob.glob(path_str)

        for file_path in f_list:
            with open(file_path, 'r') as data_file:
                data_str = data_file.read()
            data = json.loads(data_str)

            old_entries.append({
                "title": data["title"][0]["value"],
                "nid": data["nid"][0]["value"]
            })

        duplicates = set()
        for old_entry in old_entries:
            title = old_entry['title']
            ids = []
            for e in old_entries:
                if e['title'] == title:
                    ids.append(e['nid'])
            if len(ids) > 1 :
                duplicates.add(title + ' has several ids: '+str(ids))

        print(str(len(duplicates))+' duplicates:')
        for d in duplicates:
            print('\t'+d)




if __name__ == '__main__':
    unittest.main()
