import argparse
import urllib3
import json
import os
import glob
import csv
import uuid
import re
import MySQLdb

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
        #change_uuid_of_all_drupal_taxonomy_terms(args.i, connection)


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

## *****************************************************************************************

def change_uuid_of_all_drupal_taxonomy_terms(file_path, connection):
    dbBise2_dev = MySQLdb.connect(host='localhost', port=32773,  user='drupal8', passwd='drupal8', db='drupal8')
    curBise2_dev = dbBise2_dev.cursor()

    nb_created_entries = 0
    nb_updated_json_entries = 0
    nb_updated_sql_entries = 0
    edam_taxonomy = import_taxonomy_from_EDAM_BIOIMAGING_file(file_path)

    http = get_web_service(connection)
    drupal_taxonomy_names, drupal_taxonomy_json_dumps = get_taxonomy_name_list(connection)
    
    #First create all the entries that do not exist in the taxonomy
    for edam_taxonomy_entry in edam_taxonomy:
        data = json.loads(edam_taxonomy_entry)

        if name_exists(data, drupal_taxonomy_names):
            if(data["vid"][0]["target_id"] == "edam_bioimaging_operation"):
                patch_str = ''
                drupal_taxonomy_entity = get_drupal_taxonomy_entry_from_name(data, drupal_taxonomy_json_dumps)
                patch_str += '"uuid": [{"value": "' + data["uuid"][0]["value"] + '"}]'
                patch_str += ', "vid": [{"target_id": "' + data["vid"][0]["target_id"] + '"}]'
                tid = get_tid_from_name(data["name"][0]["value"], drupal_taxonomy_json_dumps)
                if tid is not None:
                    patch_str = '{' + patch_str + '}'
                    path_to_term = '/taxonomy/term/' + tid + '?_format=json'
                    updating_term = json.dumps(json.loads(patch_str)).encode('utf-8')
                    #print path_to_term
                    #print "Updating old entry " + drupal_taxonomy_entity["name"] + " with " + updating_term
                    req_import = http.request('PATCH', connection["url"] + path_to_term, body=updating_term)
                    #print(req_import.reason)
                    if 'Forbidden' in req_import.reason:
                        print (data["name"][0]["value"])
                    nb_updated_json_entries = nb_updated_json_entries + 1
                else:
                    print "**************** Problem with " + data["name"][0]["value"]
    print "Number of entries updated by json = " + str(nb_updated_json_entries)

def name_exists(json_entry, names):
    u = json_entry["name"][0]["value"]
    if u in names:
        return True
    else:
        return False

def get_taxonomy_name_list(connection):
    data, data_dumps = get_taxonomy_list(connection)
    name_set = set()
    for e in data:
        #print e
        if(e["name"] == "Clustering"):
            print "****************************************" + e["name"] + " " + e["uuid"]
        name_set.add(e["name"])
    return name_set, data_dumps

## *****************************************************************************************

def import_entry_taxonomy_from_file(file_path, connection):
    """
    Take the EDAM-BIOIMAGIN.csv file, read every taxonomy entry and put it in a string having a json type structure
    Read every taxonomy entry in the Drupal database and test every json string against the Drupal entries (test is done on the uuid attribute)
    If the taxonomy entry is not in the Drupal entries, it is added
    If the taxonomy entry is in the Drupal entries, we update any changes in the attributes
    :param file_path: the path of the EDAM-BIOIMAGING.csv file to be imported
    :param connection: the connection information (user, password, url, and proxy)
    """

    #Connection to the database of biii in drupal 8.x
    #dbBise2_dev = MySQLdb.connect(host='dbserver.dev.af5a7378-6d82-4acd-8af6-e316e51633f4.drush.in', port=13460,  user='pantheon', passwd='39be021cbee24286a3c9346cde1b44bf', db='pantheon')
    dbBise2_dev = MySQLdb.connect(host='localhost', port=32773,  user='drupal8', passwd='drupal8', db='drupal8')
    #dbBise2_dev = MySQLdb.connect(host='database.bisescratch.internal', port=3306,  user='drupal8', passwd='drupal8', db='drupal8')
    curBise2_dev = dbBise2_dev.cursor()
##    s = "SELECT ttdc.tid, ttdc.parent FROM taxonomy_term_hierarchy ttdc WHERE ttdc.tid = '%s'" % 4181 
##    curBise2_dev.execute(s)
##    res = curBise2_dev.fetchall()
##    print res
##    s = "DELETE FROM taxonomy_term_hierarchy WHERE tid = %s" % 4181
##    curBise2_dev.execute(s)
##    s = "INSERT INTO taxonomy_term_hierarchy (tid, parent) VALUES (%s, %s)" % (4181, 4032)
##    curBise2_dev.execute(s)
##    dbBise2_dev.commit()

    nb_created_entries = 0
    nb_updated_json_entries = 0
    nb_updated_sql_entries = 0
    edam_taxonomy = import_taxonomy_from_EDAM_BIOIMAGING_file(file_path)

    http = get_web_service(connection)
    drupal_taxonomy_uuids, drupal_taxonomy_json_dumps = get_taxonomy_uuid_list(connection)
    
    #First create all the entries that do not exist in the taxonomy
    for edam_taxonomy_entry in edam_taxonomy:
        #print edam_taxonomy_entry
        data = json.loads(edam_taxonomy_entry)

        #print data
        if not uuid_exists(data, drupal_taxonomy_uuids):
            encoded_entry = json.dumps(data).encode('utf-8')
            #print encoded_entry
            print data["name"][0]["value"] + " does not exist"
            nb_created_entries = nb_created_entries + 1
            req_import = http.request('POST', connection["url"] + '/entity/taxonomy_term?_format=json', body=encoded_entry)
            if 'Created' in req_import.reason:
                print(data["name"][0]["value"] + ' imported --> SUCCESS')
            else:
                #print data
                print('Import of ' + data["name"][0]["value"] + ' --> FAILED')
                print(req_import.reason)

    drupal_taxonomy_uuids, drupal_taxonomy_json_dumps = get_taxonomy_uuid_list(connection)
    
    #Then update all the taxonomy entries. Update the name/synonym/description if needed by REST/json
    #Update the parent relationship by SQL queries
    for edam_taxonomy_entry in edam_taxonomy:
        data = json.loads(edam_taxonomy_entry)

        patch_str = ''
        drupal_taxonomy_entity = get_drupal_taxonomy_entry_from_uuid(data, drupal_taxonomy_json_dumps)
        
        if(data["name"][0]["value"] != drupal_taxonomy_entity["name"]):
           patch_str += '"name": [{"value": "' + data["name"][0]["value"] + '"}]'

        if('description' in data):
            if(data["description"][0]["value"] != drupal_taxonomy_entity["description__value"]):
               if(patch_str):
                   patch_str += ', '
               patch_str += '"description": [{"value": "' + data["description"][0]["value"] + '"}]'

        if('field_synonyms' in data):
            all_synonyms = data["field_synonyms"][0]["value"].split('|')
            synonyms_str = '"field_synonyms": ['
            for syno in all_synonyms:
                synonyms_str += '{"value": "' + syno + '"},'
            synonyms_str = synonyms_str[:-1]
            synonyms_str += ']'
            #print synonyms_str
            if(patch_str):
                patch_str += ', '
            patch_str += synonyms_str
            #if(data["synonyms"][0]["value"] != drupal_taxonomy_entity["synonyms"]):
            #   if(patch_str):
            #       patch_str += ', '
            #   patch_str += '"field_synonyms": [{"value": "' + data["synonyms"][0]["value"] + '"}]'

        #if patch_str is not empty, some of the attributes of the entry have to be patched
        #to be able to patch we need to add the vocabulary of the taxonomy term (vid) no matter what, even if it the still the same 
        if(patch_str):
            patch_str += ', "vid": [{"target_id": "' + data["vid"][0]["target_id"] + '"}]'

        tid = get_tid_from_uuid(data["uuid"][0]["value"], drupal_taxonomy_json_dumps)
        
        if(patch_str):
            patch_str = '{' + patch_str + '}'
            path_to_term = '/taxonomy/term/' + tid + '?_format=json'
            updating_term = json.dumps(json.loads(patch_str)).encode('utf-8')
            print "Updating old entry " + drupal_taxonomy_entity["name"] + " with " + updating_term
            req_import = http.request('PATCH', connection["url"] + path_to_term, body=updating_term)
            nb_updated_json_entries = nb_updated_json_entries + 1

        if(data["parent"]):
            beenUpdated = False
            parents_drupal_tid = get_parents_tid_from_tid(tid, drupal_taxonomy_json_dumps)
            parent_edam_uuid = data["parent"][0]["value"].split('|')
            parents_edam_tid = list()
            for edam_uuid in parent_edam_uuid:
                tmp = get_tid_from_uuid(edam_uuid, drupal_taxonomy_json_dumps)
                if tmp:
                    parents_edam_tid.append(tmp)
            for drupal_tid in parents_drupal_tid:
                if drupal_tid not in parents_edam_tid:
                    print parents_drupal_tid
                    print "the drupal tid is not in the new hierarchy " + tid + " " + drupal_tid
                    s = "DELETE FROM taxonomy_term_hierarchy WHERE tid = %s AND parent = %s" % (tid, drupal_tid)
                    curBise2_dev.execute(s)
                    beenUpdated = True

            for edam_tid in parents_edam_tid:
                if edam_tid not in parents_drupal_tid:
                    print "the edam tid is not in the database " + tid + " " + edam_tid
                    s = "INSERT INTO taxonomy_term_hierarchy (tid, parent) VALUES (%s, %s)" % (tid, edam_tid)
                    curBise2_dev.execute(s)
                    beenUpdated = True

            if beenUpdated:
                nb_updated_sql_entries = nb_updated_sql_entries + 1
            
    print "Number of entries created = " + str(nb_created_entries)
    print "Number of entries updated by json = " + str(nb_updated_json_entries)
    print "Number of entries updated by SQL = " + str(nb_updated_sql_entries)

    dbBise2_dev.commit()
    curBise2_dev.close()
    dbBise2_dev.close()


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
                #print row
                #print ("*******************" + str(len(row)))
                uuid_t = row[0].replace("/", "\\/")
                name_t = row[1]
                synonyms_t = row[2].replace('"', '')
                definition_t = row[3].replace('"', '')#'\\"')
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
                #synonyms
                if synonyms_t:
                    jsonText += "\"field_synonyms\":[{\"value\":\"%s\"}]," % synonyms_t
                #definition
                if definition_t:
                    jsonText += "\"description\":[{\"value\":\"%s\"}]," % definition_t
                #parent
                jsonText += "\"parent\":["
                if parent_t:
                    jsonText += "{\"value\":\"%s\"}" % parent_t
                jsonText += "]}"

                #if definition_t:
                #    print jsonText
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
        if(e["name"] == "Clustering"):
            print "****************************************" + e["name"] + " " + e["uuid"]
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

def get_drupal_taxonomy_entry_from_uuid(edam_json, drupal_entries):
    for e in drupal_entries:
        if edam_json["uuid"][0]["value"] == e["uuid"]:
            return e
    return None

def get_drupal_taxonomy_entry_from_name(edam_json, drupal_entries):
    for e in drupal_entries:
        if edam_json["name"][0]["value"] == e["name"]:
            return e
    return None

def get_tid_from_uuid(uuid, drupal_entries):
    for e in drupal_entries:
        if uuid == e["uuid"]:
            return e["tid"]
    return None

def get_tid_from_name(name, drupal_entries):
    for e in drupal_entries:
        if name == e["name"]:
            return e["tid"]
    return None

def get_parents_tid_from_tid(tid, drupal_entries):
    parents_tid_set = set()
    for e in drupal_entries:
        if tid == e["tid"]:
            if e["parent"]:
                parents_tid_set.add(e["parent"])
    return parents_tid_set
                
if __name__ == '__main__':
    main()
