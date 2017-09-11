import unittest
import json
import glob
import os
import logging


class TagsTest(unittest.TestCase):

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
        cls.tags_txt = "/Users/gaignard-a/Documents/Dev/neubias-data-migration/biii-import-tool/data/TAGS.txt"

    @classmethod
    def tearDownClass(cls):
        print()

    # @unittest.skip("show tags from old drupal")
    def test_build_tags_JSON(self):
        tags = []
        if os.path.exists(self.tags_txt):
            with open(self.tags_txt,encoding='UTF-8') as f:
                while True:
                    line1 = f.readline().strip().replace(',','')
                    line2 = f.readline().strip().replace(',','')
                    if not line2: break  # EOF
                    name = line1.split('Name: ', maxsplit=1)[1]
                    tagid = line2.split('Term ID: ', maxsplit=1)[1]
                    # print (name + ' || ' + tagid)
                    tag_entry = {
                        'id': tagid,
                        'name': name
                    }
                    tags.append(tag_entry)
            print(json.dumps(tags, indent=4))
        else:
            print('Could not find file '+self.tags_txt)

if __name__ == '__main__':
    unittest.main()
