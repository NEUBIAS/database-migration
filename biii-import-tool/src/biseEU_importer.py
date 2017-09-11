import argparse
import urllib3
import json
import os
import glob

# import logging

# logger = logging.getLogger('biseEU_importer')
# logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
# ch.setFormatter(formatter)
# logger.addHandler(ch)

# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

parser = argparse.ArgumentParser(description="""
JSON import tool for the NeuBIAS Bise.eu registry.

Sample Usage :  
    python biseEU_importer.py -u <USERNAME> -p <PASSWORD> -td http://dev-bise2.pantheonsite.io -px http://cache.ha.univ-nantes.fr:3128 -d ../data/small_set/ 
    python biseEU_importer.py -u <USERNAME> -p <PASSWORD> -td http://dev-bise2.pantheonsite.io -px http://cache.ha.univ-nantes.fr:3128 -i ../data/small_set/node3.json 
                                 """)
parser.add_argument('-px', '--proxy', metavar='proxy', type=str, help='your proxy URL, including the proxy port',
                    dest='px', required=False)
parser.add_argument('-td', '--target_drupal_url', metavar='target_drupal_url', type=str, help='the target drupal url',
                    dest='td', required=True)
parser.add_argument('-u', '--username', metavar='username', type=str, help='username', dest='u', required=True)
parser.add_argument('-p', '--password', metavar='password', type=str, help='password', dest='p', required=True)
parser.add_argument('-i', '--input_file', metavar='input_directory', type=str, help='the JSON file to be imported',
                    dest='i',
                    required=False)
parser.add_argument('-d', '--input_directory', metavar='input_directory', type=str,
                    help='the JSON file directory to be imported', dest='d', required=False)


def main():
    print('NeuBIAS import tool - v0.1a')
    args = parser.parse_args()

    if args.td is None:
        print('Please fill the -td or --target_drupal_url parameter')
        parser.print_usage()
        exit(0)
    if args.u is None:
        print('Please fill the -u or --username parameter')
        parser.print_usage()
        exit(0)
    if args.p is None:
        print('Please fill the -p or --password parameter')
        parser.print_usage()
        exit(0)
    if (args.i is None) and (args.d is None):
        print('Please fill the -i or -d parameters')
        parser.print_usage()
        exit(0)

    connection = {
        'username': args.u,
        'password': args.p,
        'url': args.td,
        'proxy': args.px
    }

    if args.i:
        import_entry(args.i, connection)
    if args.d:
        import_directory(args.d, connection)


def get_web_service(connection):
    """
    establish an HTTP connection based on url, user, password, and proxy given in parameter  
    :param connection: the connection information (user, password, url, and proxy)
    :return: an urllib3 PoolManager instance connected to the endpoint url
    """
    http = urllib3.PoolManager()
    auth_header = urllib3.util.make_headers(basic_auth=connection["username"] + ':' + connection["password"])
    if ('proxy' in connection.keys()) and connection["proxy"]:
        http = urllib3.ProxyManager(connection["proxy"], headers=auth_header)
    http.headers.update(auth_header)
    http.headers['Accept'] = 'application/json'
    http.headers['Content-type'] = 'application/json'
    return http


def import_directory(path_str, connection):
    """
    Iterates over a file directory and import each JSON file
    :param path_str: the path of the JSON directory to be imported
    :param connection: the connection information (user, password, url, and proxy)
    """
    list = glob.glob(path_str + "/*.json")
    for f_name in list:
        import_entry(f_name, connection)


def import_entry(file_path, connection):
    """
    Imports an entry to the Drupal backend via its REST API 
    :param file_path: the path of the JSON file to be imported
    :param connection: the connection information (user, password, url, and proxy)
    :return: a server string message, null if the import was not processed
    """
    if os.path.exists(file_path):
        http = get_web_service(connection)
        with open(file_path, 'r') as data_file:
            data_str = data_file.read()
        data = json.loads(data_str)
        titles = get_software_title_list(connection)

        if not title_exists(data, titles):
            data = remove_id(data)
            data = remove_dependencies(data)
            data = patch_with_entry_curator(data, "98")
            data = validate_doi(data)
            if data["field_license_openness"][0]["target_id"] == "3570":
                data = patch_with_licence_id(data, "3578")
            encoded_entry = json.dumps(data).encode('utf-8')
            req_import = http.request('POST', connection["url"] + '/entity/node?_format=json', body=encoded_entry)
            if 'Created' in req_import.reason:
                print(file_path + ' imported --> SUCCESS')
            else:
                print('Import of ' + file_path + ' --> FAILED')
                print('\t' + req_import.reason)
            return req_import.reason
        else:
            print('Skipping ' + file_path + ': ' + data["title"][0]["value"] + ' already exists')

    else:
        print("Failed to import " + file_path)
        print(file_path + " does not exists")


def validate_doi(json_entry):
    if ('field_has_reference_publication' in json_entry) and json_entry["field_has_reference_publication"]:
        doi = str(json_entry["field_has_reference_publication"][0]["uri"])
        if not doi.startswith("http://"):
            json_entry["field_has_reference_publication"][0]["uri"] = "http://" + str(
                json_entry["field_has_reference_publication"][0]["uri"])
    return json_entry


def remove_id(json_entry):
    json_entry.pop('nid', None)
    json_entry.pop('vid', None)
    json_entry.pop('uuid', None)
    return json_entry


def remove_dependencies(json_entry):
    json_entry.pop('field_is_dependent_of', None)
    return json_entry


def patch_with_entry_curator(json_entry, curator_id):
    if json_entry["field_has_entry_curator"][0]["target_id"]:
        json_entry["field_has_entry_curator"][0]["target_id"] = curator_id
    return json_entry


def patch_with_licence_id(json_entry, license_id):
    if json_entry["field_license_openness"][0]["target_id"]:
        json_entry["field_license_openness"][0]["target_id"] = license_id
        # print(json.dumps(json_entry, indent=4, sort_keys=True))
        # print("--> Patched entry " + str(json_entry["vid"]) + " with licence "+str(json_entry["field_license_openness"][0]
        #                                                                        ["target_id"]))
    return json_entry


def title_exists(json_entry, titles):
    t = json_entry["title"][0]["value"]
    if t in titles:
        return True
    else:
        return False


def get_software_title_list(connection):
    data = get_software_list(connection)
    title_set = set()
    for e in data:
        title_set.add(e["title"])
    return title_set


def get_software_list(connection):
    """
    Get the JSON ouput of the Software view of the drupal site given in parameter
    :param connection:
    :return:
    """
    http = get_web_service(connection)
    try:
        req = http.request('GET', connection["url"] + '/soft/?_format=json')
        data = json.loads(req.data.decode('utf-8'))
        # print(json.dumps(data, indent=4, sort_keys=True))
        return data
    except urllib3.exceptions.HTTPError as e:
        print("Connection error")
        print(e)


def get_software_node_id(connection, title):
    """
    Query the Drupal REST API and return the ID corresponding to the title
    :param connection:
    :param title:
    :return: the entry ID if found, None otherwise
    """
    http = get_web_service(connection)
    try:
        req = http.request('GET', connection["url"] + '/soft/?_format=json')
        data = json.loads(req.data.decode('utf-8'))
        # print(json.dumps(data, indent=4, sort_keys=True))
        for entry in data:
            # print(title+" ?+? "+str(entry["title"]))
            if title == entry["title"]:
                return entry["nid"]
        return None

    except urllib3.exceptions.HTTPError as e:
        print("Connection error")
        print(e)
        return None


def update_dependencies_in_directory(path_str, connection):
    """
    Iterates over a file directory (OLD entries) and build a JSON object with title-id-dependencies associations
    Then from these dependecies, update the new entry ID with its dependencies (new IDs)
    :param path_str: the path of the JSON directory to be imported
    :param connection: the connection information (user, password, url, and proxy)
    """
    old_entries = []
    f_list = glob.glob(path_str)
    new_entries = get_software_list(connection)

    for file_path in f_list:
        with open(file_path, 'r') as data_file:
            data_str = data_file.read()
        data = json.loads(data_str)

        old_entries.append({
            "title": data["title"][0]["value"],
            "nid": data["nid"][0]["value"],
            "dependencies": data["field_is_dependent_of"]
        })

    for old_entry in old_entries:
        if old_entry['dependencies']:
            print('Processing ' + old_entry['title'])
            deps = []
            if get_software_from_title(new_entries, old_entry['title']):
                new_id = get_software_from_title(new_entries,old_entry['title'])['nid']
                for d in old_entry['dependencies']:
                    dep = get_software_from_id(old_entries,d['target_id'])
                    # print(old_entry['title']+" -- depends on --> "+str(dep['title']))
                    if get_software_from_title(new_entries,str(dep['title'])):
                        # print('\tnew IDs :: '+get_software_from_title(new_entries,old_entry['title'])['nid']
                        #    + " -- depends on --> " +get_software_from_title(new_entries,str(dep['title']))['nid'])
                        deps.append(get_software_from_title(new_entries,str(dep['title']))['nid'])
                    else:
                        print('!! Missing imported entries ')
                        print('\t' + old_entry['title'] + ' or ' + str(dep['title']))

                update_dependency(new_id,
                              deps,
                              connection)
            else:
                print(print('!! Missing entry '+old_entry['title']))
            print()


def update_dependency(source_id, target_ids, connection):
    """
    HTTP PATCH query to update dependencies
    """
    print('updating ' + str(source_id) + ' with dependencies ' + str(target_ids))
    http = get_web_service(connection)

    # only send the changed part of the entry
    data = { 'field_is_dependent_of':[],
             'type': [{'target_id': 'software'}]}
    for d in target_ids:
        data['field_is_dependent_of'].append({ 'target_id': str(d)})
    # print(json.dumps(data, indent=4))
    encoded_entry = json.dumps(data).encode('utf-8')
    req_update = http.request('PATCH', connection["url"] + '/node/'+str(source_id)+'?_format=json',
                              body=encoded_entry)
    if not 'OK' in req_update.reason:
        print('!! error when updating dependencies of node '+source_id)


def get_software_from_title(json, title):
    for e in json:
        if e["title"] == title:
            return e
    return None


def get_software_from_id(json, id):
    for e in json:
        if str(e["nid"]) == str(id):
            return e
    return None


if __name__ == '__main__':
    main()
