import argparse
import urllib3
import json
import os
import glob
import csv
import uuid
import re

#python.exe biseEU_importer_taxonomy.py -u flevet -p xxx -td http://dev-bise2.pantheonsite.io -i EDAM-bioimaging_alpha03.tsv
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
    #import_entry_taxonomy_from_file('D:\Biii\EDAM-BIOIMAGING.csv', 'test')
    #print('NeuBIAS import tool - v0.1a')
    args = parser.parse_args()

    if args.td is None:
        print('Please fill the -td or --target_drupal_url parameter')
        parser.print_help()
        exit(0)
    if args.u is None:
        print('Please fill the -u or --username parameter')
        parser.print_help()
        exit(0)
    if args.p is None:
        print('Please fill the -p or --password parameter')
        parser.print_help()
        exit(0)
    if (args.i is None) and (args.d is None):
        print('Please fill the -i or -d parameters')
        parser.print_help()
        exit(0)

    connection = {
        'username': args.u,
        'password': args.p,
        'url': args.td,
        'proxy': args.px
    }

    if args.i:
        import_entry_taxonomy_from_file(args.i, connection)


def get_web_service(connection):
    """
    establish an HTTP connection based on url, user, password, and proxy given in parameter  
    :param connection: the connection information (user, password, url, and proxy)
    :return: an urllib3 PoolManager instance connected to the endpoint url
    """
    http = urllib3.PoolManager()
    auth_header = urllib3.util.make_headers(basic_auth=connection["username"] + ':' + connection["password"])
    if ('proxy_url' in connection.keys()) and connection["proxy_url"]:
        http = urllib3.ProxyManager(connection["proxy_url"], headers=auth_header)
    http.headers.update(auth_header)
    http.headers['Accept'] = 'application/json'
    http.headers['Content-type'] = 'application/json'
    return http

def import_entry_taxonomy_from_file(file_path, connection):
    """
    Take the EDAM-BIOIMAGIN.csv file, read every taxonomy entry and put it in a string having a json type structure
    Read every taxonomy entry in the Drupal database and test every json string against the Drupal entries (test is done on the uuid attribute)
    If the taxonomy entry is not in the Drupal entries, it is added
    If the taxonomy entry is in the Drupal entries, we update any changes in the attributes
    :param file_path: the path of the EDAM-BIOIMAGING.csv file to be imported
    :param connection: the connection information (user, password, url, and proxy)
    """
    http = get_web_service(connection)
    drupal_taxonomy_uuids, drupal_taxonomy_json_dumps = get_taxonomy_uuid_list(connection)
    #print drupal_taxonomy_uuids

    #for entry in drupal_taxonomy_json_dumps:
    #    print entry["name"]

    
    path_to_term = '/taxonomy/term/' + str(4343) + '?_format=json'

    dataTmp = { 'name': [{'value': 'testTaxoChanged'}]}
         
    updating_term = json.dumps(dataTmp).encode('utf-8')# json.dumps(json.loads("{\"name\":[{\"value\":\"testTaxoChanged\"}]}")).encode('utf-8')
    print updating_term
    print connection["url"] + path_to_term
    req_import = http.request('PATCH', connection["url"] + path_to_term, body=updating_term)
    print req_import.reason

    nb_created_entries = 0
    nb_updated_entries = 0
    edam_taxonomy = import_taxonomy_from_EDAM_BIOIMAGING_file(file_path)
    for edam_taxonomy_entry in edam_taxonomy:
        data = json.loads(edam_taxonomy_entry)

        if not uuid_exists(data, drupal_taxonomy_uuids):
            encoded_entry = json.dumps(data).encode('utf-8')
            #print encoded_entry
            #print data["name"][0]["value"] + " does not exist"
            nb_created_entries = nb_created_entries + 1
##            req_import = http.request('POST', connection["url"] + '/entity/taxonomy_term?_format=json', body=encoded_entry)
##            if 'Created' in req_import.reason:
##                print(file_path + ' imported --> SUCCESS')
##            else:
##                print('Import of ' + file_path + ' --> FAILED')
##                print('\t' + req_import.reason)
##            return req_import.reason
        else:
##            print('Skipping ' + data["name"][0]["value"] + ' already exists')
##
##            tid = get_tid_from_uuid(data, drupal_taxonomy_json_dumps)
##            if tid:
##                print "The tid of the element " + data["name"][0]["value"] + ", " + data["uuid"][0]["value"] + " is " + tid
##            else:
##                print "No tid found the element " + data["name"][0]["value"] + ", " + data["uuid"][0]["value"]
            
            nb_updated_entries = nb_updated_entries + 1
            
    print "Number of entries created = " + str(nb_created_entries)
    print "Number of entries updated = " + str(nb_updated_entries)


def import_taxonomy_from_EDAM_BIOIMAGING_file(file_path):
    taxonomy_list = []
    if os.path.exists(file_path):
        vidOperation = "edam_bioimaging_operation"
        vidTopic = "edam_bioimaging_topic"
        vidFormat = "edam_bioimaging_format"
        vidData = "edam_bioimaging_data"
        vidTags = "edam_bioimaging"
        #Import the taxonomy related to edam-bioimaging. We directly create 4 vocabulaires related to operation, topic, data and format
        currentTerm = 1
        with open(file_path, 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter='\t', quotechar='|')
            next(csvfile)
            for row in spamreader:
                uuid_t = row[0].replace("/", "\\/")
                name_t = row[1]
                vid_t = vidTags
                parent_t = ""
                if "owl" not in row[7]:
                    parent_t = row[7].replace("/", "\\/")
                if "operation" in uuid_t.lower():
                    vid_t = vidOperation
                if "topic" in uuid_t.lower():
                    vid_t = vidTopic
                if "format" in uuid_t.lower():
                    vid_t = vidFormat
                if "data" in uuid_t.lower():
                    vid_t = vidData

                jsonText = "{"
                #nid
                jsonText += "\"uuid\":[{\"value\":\"%s\"}]," % uuid_t
                #vid
                jsonText += "\"vid\":[{\"target_id\":\"%s\"}]," % vid_t
                #name
                jsonText += "\"name\":[{\"value\":\"%s\"}]," % name_t
                #parent
                jsonText += "\"parent\":["
                if parent_t:
                    jsonText += "{\"value\":\"%s\"}" % parent_t
                jsonText += "]}"

                #print jsonText
                taxonomy_list.append(jsonText)
    return taxonomy_list

def uuid_exists(json_entry, uuids):
    u = json_entry["uuid"][0]["value"]
    if u in uuids:
        return True
    else:
        return False

def get_taxonomy_uuid_list(connection):
    data, data_dumps = get_taxonomy_list(connection)
    uuid_set = set()
    for e in data:
        #print e
        uuid_set.add(e["uuid"])
    return uuid_set, data_dumps

def get_taxonomy_list(connection):
    """
    Get the JSON output of the Taxonomy view of the drupal site given in parameter
    :param connection:
    :return:
    """
    http = get_web_service(connection)
    try:
        req = http.request('GET', connection["url"] + '/taxo/?_format=json')
        #print req
        data = json.loads(req.data.decode('utf-8'))
        data_dumps = json.loads(req.data.decode('utf-8'))
        #data_dumps = [ json.dumps(entry).encode('utf-8') for entry in data]
        #print data
        return data, data_dumps
    except urllib3.exceptions.HTTPError as e:
        print("Connection error")
        print(e)

def get_tid_from_uuid(edam_json, drupal_entries):
    for e in drupal_entries:
        drupal_uuid = edam_json["uuid"][0]["value"]
        if edam_json["uuid"][0]["value"] == e["uuid"]:
            return e["tid"]
    return None

#def check_if_name_has_changed(json_entry):
                

def validate_doi(json_entry):
    """
    :param json_entry:
    :return: if a DOI don't starts with http://, returns a DOI prefixed with http://
    """
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
        try:
            data = json.loads(data_str)
        except json.decoder.JSONDecodeError as e:
            print("parsing ERROR "+e.msg)

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
                    if not dep is None:
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
                print('!! Missing entry '+old_entry['title'])
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
