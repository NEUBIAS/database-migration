import unittest
import json
import glob
import os
import urllib3.exceptions
import logging

from src.biseEU_importer import get_software_list
from src.biseEU_importer import get_web_service
from src.biseEU_importer import get_software_from_title

class UsersTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.connection = {
            'username': 'USERNAME',
            'password': 'PASSWORD',
            'url': 'http://dev-bise2.pantheonsite.io',
            'proxy': 'PROXY URL'
        }
        cls.jsonFile = "./data/dump/nodes_software/node2098.json"
        cls.jsonDir = "./data/dump/nodes_software"
        cls.users_txt = "/Users/gaignard-a/Documents/Dev/neubias-data-migration/biii-import-tool/data/users.txt"
        cls.curators_txt = "/Users/gaignard-a/Documents/Dev/neubias-data-migration/biii-import-tool/data/activecurators.txt"

    @classmethod
    def tearDownClass(cls):
        print()

    @unittest.skip("show users from old drupal")
    def test_build_users_JSON(self):
        users = self.get_users()
        print(json.dumps(users, indent=4))

    @unittest.skip("register active curators from old drupal")
    def test_register_curators_JSON(self):
        curators = self.get_active_curators()
        self.register_curators(curators)

    @unittest.skip("test_fake_user_import")
    def test_fake_user_import(self):
        # test_migration/test_migration
        data = {
            'name': [{'value': 'test_migration'}],
            'mail': [{'value': 'alban.gaignard@gmail.com'}]
        }
        encoded_entry = json.dumps(data).encode('utf-8')
        http = get_web_service(self.connection)
        req_user_register = http.request('POST', self.connection["url"] + '/entity/user?_format=json',
                                         body=encoded_entry)
        if 'Created' in req_user_register.reason:
            print('Successfully imported user ' + str(data['mail']))
        elif 'Forbidden' in req_user_register.reason:
            print('Forbidden import')
        else:
            print('User ' + str(data) + ' already exists')


    @unittest.skip("update entries with their curators")
    def test_update_entry_curators(self):
        # curators = self.get_active_curators()
        # print(json.dumps(curators, indent=4))
        # print()
        # all_users = self.get_user_list(self.connection)
        # print(json.dumps(all_users, indent=4))
        # print()
        self.update_curators()

    def get_user_list(self, connection):
        """
        Get the JSON ouput of the Users view of the drupal site given in parameter
        :param connection:
        :return:
        """
        http = get_web_service(connection)
        try:
            req = http.request('GET', connection["url"] + '/users/?_format=json')
            data = json.loads(req.data.decode('utf-8'))
            # print(json.dumps(data, indent=4, sort_keys=True))
            return data
        except urllib3.exceptions.HTTPError as e:
            print("Connection error")
            print(e)

    def register_curators(self, list_of_curators):
        old_users = self.get_users()
        to_be_registered = set()
        for curator in list_of_curators:
            if curator['author_id'] != "0":
                user = self.get_user_from_id(curator['author_id'], old_users)
                if user['id'] not in to_be_registered:
                    to_be_registered.add(user['id'])
                    print('Registering ' + str(user))
                    data = {
                        'name': [{'value': user['login']}],
                        'mail': [{'value': user['email']}]
                    }
                    encoded_entry = json.dumps(data).encode('utf-8')
                    # http = get_web_service(self.connection)
                    # req_user_register = http.request('POST', self.connection["url"] + '/entity/user?_format=json',
                    #                                  body=encoded_entry)
                    # if 'Created' in req_user_register.reason:
                    #     print('Successfully imported user ' + str(data['mail']))
                    # else:
                    #     print('User ' + str(data) + ' already exists')

    def get_user_from_login(self, login, json):
        for u in json:
            if str(u['name']).lower() == str(login).lower():
                return u
        return None

    def update_curators(self):
        curators = self.get_active_curators()
        old_users = self.get_users()
        new_users = self.get_user_list(self.connection)
        new_softwares = get_software_list(self.connection)

        for item in curators:
            entry_title = item['entry_title']
            software = get_software_from_title(new_softwares, entry_title)
            curator_old_id = item['author_id']
            user = self.get_user_from_id(curator_old_id,old_users)
            if (not user is None) and (not software is None):
                # print('Setting curator for '+entry_title+' with')
                # print('\t OLD: '+str(user))
                new_user = self.get_user_from_login(user['login'],new_users)
                # print('\t NEW: '+str(new_user))
                if not new_user is None:
                    # print('\t\t'+str(software))
                    self.update_entry_curator(software['nid'], new_user['uid'], self.connection)

    def update_entry_curator(self, soft_id, user_id, connection):
        """
        HTTP PATCH query to update curators
        """
        print('updating node ' + str(soft_id) + ' with curator ' + str(user_id))
        http = get_web_service(connection)

        # only send the changed part of the entry
        data = {'field_has_entry_curator': [{'target_id': user_id}],
                'type': [{'target_id': 'software'}]}
        # print(json.dumps(data, indent=4))
        encoded_entry = json.dumps(data).encode('utf-8')
        req_update = http.request('PATCH', connection["url"] + '/node/' + str(soft_id) + '?_format=json',
                                  body=encoded_entry)
        if not 'OK' in req_update.reason:
            print('!! error when updating curator of node ' + soft_id)

    def get_user_from_id(self, target_id, json):
        for u in json:
            if u['id'] == target_id:
                return u
        return None

    def get_active_curators(self):
        users = []
        if os.path.exists(self.curators_txt):
            with open(self.curators_txt, encoding='UTF-8') as f:
                while True:
                    line1 = f.readline().strip()
                    line2 = f.readline().strip()
                    line3 = f.readline().strip()
                    if not line3: break  # EOF

                    entry_title = line1
                    author_id = line2.split('Author uid: ', maxsplit=1)[1]
                    entry_id = line3.split('Nid: ', maxsplit=1)[1]
                    user_entry = {
                        'entry_title': entry_title,
                        'author_id': author_id,
                        'entry_id': entry_id,
                    }
                    users.append(user_entry)
            return users
        else:
            print('Could not find file ' + self.curators_txt)
            return None

    def get_users(self):
        users = []
        if os.path.exists(self.users_txt):
            with open(self.users_txt, encoding='UTF-8') as f:
                while True:
                    line1 = f.readline().strip()
                    line2 = f.readline().strip()
                    line3 = f.readline().strip()
                    line4 = f.readline().strip()
                    if not line4: break  # EOF

                    login = line1
                    email = line2.split('E-mail: ', maxsplit=1)[1]
                    uid = line3.split('Uid: ', maxsplit=1)[1]
                    # print(login + ' || ' + email + ' || ' + uid)
                    user_entry = {
                        'id': uid,
                        'login': login,
                        'email': email,
                    }
                    users.append(user_entry)
            # print(json.dumps(users, indent=4))
            return users
        else:
            print('Could not find file ' + self.users_txt)
            return None

if __name__ == '__main__':
    unittest.main()
