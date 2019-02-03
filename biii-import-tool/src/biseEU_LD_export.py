import urllib3
import json
import argparse
from argparse import RawTextHelpFormatter
import time
import datetime
import sys
from rdflib import Graph

from src.biseEU_importer import get_web_service
from src.biseEU_importer import get_software_list

parser = argparse.ArgumentParser(description="""
RDF export tool for the NeuBIAS Bise.eu registry.

Sample Usage :
    python biseEU_LD_export.py -u <USERNAME> -p <PASSWORD> -td http://dev-bise2.pantheonsite.io -px <PROXY_URL> -id 67
    python biseEU_LD_export.py -u <USERNAME> -p <PASSWORD> -td http://dev-bise2.pantheonsite.io -px <PROXY_URL> -test
    python biseEU_LD_export.py -u <USERNAME> -p <PASSWORD> -td http://dev-bise2.pantheonsite.io -px <PROXY_URL> -dump  
                                 """, formatter_class=RawTextHelpFormatter)
parser.add_argument('-px', '--proxy', metavar='proxy', type=str, help='your proxy URL, including the proxy port',
                    dest='px', required=False)
parser.add_argument('-td', '--target_drupal_url', metavar='target_drupal_url', type=str, help='the target drupal url',
                    dest='td', required=True)
parser.add_argument('-u', '--username', metavar='username', type=str, help='username', dest='u', required=True)
parser.add_argument('-p', '--password', metavar='password', type=str, help='password', dest='p', required=True)
parser.add_argument('-id', '--node_id', metavar='node_id', type=str, help='the ID of the Bise resource to be exported', dest='id', required=False)
parser.add_argument('-dump', '--dump_all', help='RDF dump all Bise resources in RDF', dest='dump', action='store_true', required=False)
parser.add_argument('-test', '--test_dump', help='test the RDF dump on the first 10 Bise resources in RDF', dest='test', action='store_true', required=False)


def main():
    #print('NeuBIAS LD export tool - v0.1a')
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
    if (args.id is None) and (args.dump is False) and (args.test is False):
        print('Please fill the -id, -dump, or -test parameters')
        parser.print_help()
        exit(0)

    connection = {
        'username': args.u,
        'password': args.p,
        'url': args.td,
        'proxy': args.px
    }

    if args.id:
        graph = Graph()
        raw_jld = get_node_as_linked_data(args.id, connection)
        # raw_jld = get_node_as_bioschema(args.id, connection)
        import_to_graph(graph, raw_jld)
        sys.stdout.buffer.write(graph.serialize(format='turtle'))
        # print(str(graph.serialize(format='turtle').decode('utf-8')))

    if args.test:
        softwares = get_software_list(connection)
        total = len(softwares)
        graph = Graph()
        count = 0
        for s in softwares:
            sys.stdout.buffer.write(
                'Exporting '.encode('utf-8') + s['title'].encode('utf-8') + ': '.encode('utf-8') + s['nid'].encode(
                    'utf-8') + ' ['.encode('utf-8') + str(round(count * 100 / total)).encode(
                    'utf-8') + '% done]\n'.encode('utf-8'))
            sys.stdout.flush()
            node_ld = get_node_as_linked_data(s['nid'], connection)
            # node_ld = get_node_as_bioschema(s['nid'], connection)
            import_to_graph(graph, node_ld)
            count += 1
            if count > 10:
                break
        # print(str(graph.serialize(format='turtle').decode('utf-8')))

        graph.serialize(destination='neubias-test-' + time.strftime("%Y%m%d") + '.ttl', format='turtle',
                        encoding='utf-8')
        graph.serialize(destination='neubias-test-' + time.strftime("%Y%m%d") + '.json-ld', format='json-ld',
                        encoding='utf-8')

    if args.dump:
        softwares = get_software_list(connection)
        total = len(softwares)
        graph = Graph()
        count = 0
        for s in softwares:
            sys.stdout.buffer.write('Exporting '.encode('utf-8') + s['title'].encode('utf-8') + ': '.encode('utf-8') + s['nid'].encode('utf-8') + ' ['.encode('utf-8') + str(round(count * 100 / total)).encode('utf-8') + '% done]\n'.encode('utf-8'))
            sys.stdout.flush()
            node_ld = get_node_as_linked_data(s['nid'], connection)
            # node_ld = get_node_as_bioschema(s['nid'], connection)
            import_to_graph(graph, node_ld)
            count += 1
            # if count > 10:
            #     break
        # print(str(graph.serialize(format='turtle').decode('utf-8')))

        graph.serialize(destination='neubias-dump-' + time.strftime("%Y%m%d") + '.ttl', format='turtle', encoding='utf-8')
        graph.serialize(destination='neubias-dump-' + time.strftime("%Y%m%d") + '.json-ld', format='json-ld', encoding='utf-8')


def get_node_as_linked_data(node_id, connection):
    """
    Transforms a Drupal node (http://biii.eu) of type Software into RDF, using Bise core
    and EDAM-Bioimaging ontologies
    :param node_id: the drupal ID of the node for online retrieval
    :param connection: credentials, possibly proxy, and URL to connect to
    :return: a string representation of the corresponding JSON-LD document
    """
    http = get_web_service(connection)
    try:
        req = http.request('GET', connection["url"] + '/node/' + str(node_id) + '?_format=json')
        entry = json.loads(req.data.decode('utf-8'))
        # print(json.dumps(entry, indent=4, sort_keys=True))
        # print()
        return rdfize(entry)
    except urllib3.exceptions.HTTPError as e:
        print("Connection error")
        print(e)
        return None

def get_node_as_bioschema(node_id, connection):
    """
    Transforms a Drupal node (http://biii.eu) of type Software into RDF, using Bioschema
    and EDAM-Bioimaging ontologies
    :param node_id: the drupal ID of the node for online retrieval
    :param connection: credentials, possibly proxy, and URL to connect to
    :return: a string representation of the corresponding JSON-LD document
    """
    http = get_web_service(connection)
    try:
        req = http.request('GET', connection["url"] + '/node/' + str(node_id) + '?_format=json')
        entry = json.loads(req.data.decode('utf-8'))
        # print(json.dumps(entry, indent=4, sort_keys=True))
        # print()
        return rdfize_bioschema_tool(entry)
    except urllib3.exceptions.HTTPError as e:
        print("Connection error")
        print(e)
        return None

def rdfize_bioschema_tool(json_entry):
    entry = json_entry
    # print(json.dumps(entry, indent=4, sort_keys=True))

    ctx = {
        "@context": {
            "@base": "http://schema.org/",
            "dc": "http://dcterms/",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "description": "http://schema.org/description",
            "citation": "http://schema.org/citation",
            "name": "http://schema.org/name",
            "featureList": "http://schema.org/featureList",
            "license": "http://schema.org/license",
            "publisher": "http://schema.org/publisher",
            "applicationCategory": "http://schema.org/applicationCategory",
            "dateCreated": "http://schema.org/dateCreated",
            "dateModified": "http://schema.org/dateModified",
            "softwareRequirements": "http://schema.org/softwareRequirements"
        }
    }

    out = {}
    # this data export only apply to softwares, so we check first if the type is a software
    if str(entry["type"][0]["target_id"]) == 'software':
        out["@id"] = "http://biii.eu/node/" + str(entry["nid"][0]["value"])
        out["@type"] = "SoftwareApplication"

        if entry["body"] and entry["body"][0] and entry["body"][0]["value"]:
            out["description"] = entry["body"][0]["value"]

        if entry["title"] and entry["title"][0] and entry["title"][0]["value"]:
            out["name"] = entry["title"][0]["value"]

        for item in entry['field_has_function']:
            if "target_uuid" in item.keys():
                if not "featureList" in out.keys():
                    out["featureList"] = [{"@id": item["target_uuid"]}]
                else:
                    out["featureList"].append({"@id": item["target_uuid"]})

                if not "applicationCategory" in out.keys():
                    out["applicationCategory"] = [{"@id": item["target_uuid"]}]
                else:
                    out["applicationCategory"].append({"@id": item["target_uuid"]})

        for item in entry['field_has_reference_publication']:
            if not "citation" in out.keys():
                out["citation"] = []
            if item["uri"]:
                out["citation"].append({"@id": item["uri"].strip()})
            if item["title"]:
                out["citation"].append(item["title"])

        for item in entry['field_has_license']:
            if not "license" in out.keys():
                out["license"] = []
            if item["value"]:
                out["license"].append(item["value"])

        for item in entry['field_has_author']:
            if not "publisher" in out.keys():
                out["publisher"] = []
            if item["value"]:
                out["publisher"].append(item["value"])

        for item in entry['created']:
            if item["value"]:
                date = datetime.datetime.fromtimestamp(item["value"])
                out["dateCreated"] = str(date.isoformat())

        for item in entry['changed']:
            if item["value"]:
                date = datetime.datetime.fromtimestamp(item["value"])
                out["dateModified"] = str(date.isoformat())

        for item in entry['field_is_dependent_of']:
            if not "softwareRequirements" in out.keys():
                out["softwareRequirements"] = []
            if item["target_id"]:
                out["softwareRequirements"].append({"@id": "http://biii.eu/node/" +
                                                           str(item["target_id"])})

        out.update(ctx)

    # print(json.dumps(out, indent=4, sort_keys=True))

    raw_jld = json.dumps(out)
    return raw_jld

def rdfize(json_entry):

    try :
        entry = json_entry
        # print(json.dumps(entry, indent=4, sort_keys=True))
        # print()

        ctx = {
            "@context": {
                "@base": "http://biii.eu/node/",
                "nb": "http://bise-eu.info/core-ontology#",
                "dc": "http://dcterms/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",

                "hasDescription": "rdfs:comment",
                "hasTitle": "dc:title",

                "hasAuthor": "nb:hasAuthor",
                "hasFunction": "nb:hasFunction",
                "hasTopic": "nb:hasTopic",
                "hasIllustration": "nb:hasIllustration",
                "requires": "nb:requires",
                "citation": "nb:hasReferencePublication",
                "location": "nb:hasLocation",
            }
        }
        entry["@id"] = str(entry["nid"][0]["value"])
        entry["@type"] = str(entry["type"][0]["target_id"])
        entry.update(ctx)

        ######
        if entry["body"] and entry["body"][0] and entry["body"][0]["value"] :
            entry["hasDescription"] = entry["body"][0]["value"]

        if entry["title"] and entry["title"][0] and entry["title"][0]["value"]:
            entry["hasTitle"] = entry["title"][0]["value"]

        for item in entry['field_image']:
            if not "hasIllustration" in entry.keys():
                entry["hasIllustration"] = [item["url"]]
            else:
                entry["hasIllustration"].append(item["url"])

        for item in entry['field_has_author']:
            if not "hasAuthor" in entry.keys():
                entry["hasAuthor"] = []
            if item["value"]:
                entry["hasAuthor"].append(item["value"])

        # for item in entry['field_has_entry_curator']:
            # print(item)

        for item in entry['field_has_function']:
            # print(item)
            if "target_uuid" in item.keys():
                if not "hasFunction" in entry.keys():
                    entry["hasFunction"] = [{"@id": item["target_uuid"]}]
                else:
                    entry["hasFunction"].append({"@id": item["target_uuid"]})

        for item in entry['field_has_topic']:
            # print(item)
            if "target_uuid" in item.keys():
                if not "hasTopic" in entry.keys():
                    entry["hasTopic"] = [{"@id": item["target_uuid"]}]
                else:
                    entry["hasTopic"].append({"@id": item["target_uuid"]})

        for item in entry['field_is_dependent_of']:
            # print(item)
            if "target_id" in item.keys():
                if not "requires" in entry.keys():
                    entry["requires"] = [{"@id": "http://biii.eu/node/"+str(item["target_id"])}]
                else:
                    entry["requires"].append({"@id": "http://biii.eu/node/"+str(item["target_id"])})

        for item in entry['field_has_reference_publication']:
            if not "citation" in entry.keys():
                entry["citation"] = []
            if item["uri"]:
                entry["citation"].append({"@id": item["uri"].strip()})
            if item["title"]:
                entry["citation"].append(item["title"])

        for item in entry['field_has_location']:
            if not "location" in entry.keys():
                entry["location"] = []
            if item["uri"]:
                entry["location"].append({"@id": item["uri"].strip()})
            if item["title"]:
                entry["location"].append(item["title"])
    except KeyError as e:
        print(e)
        print(json.dumps(entry, indent=4, sort_keys=True))
        sys.exit(-1)

    raw_jld = json.dumps(entry)
    return raw_jld


def import_to_graph(graph, raw_jld):
    """
    Parse a JSON-LD document and add it to an in-memory RDF graph
    :param graph: an in-memory RDF graph
    :param raw_jld: a string representation of a JSON-LD document
    :return: the populated RDF graph
    """
    g = graph
    g.parse(data=raw_jld, format='json-ld')
    # print(g.serialize(format='turtle').decode('utf-8'))
    # print()
    # print(g.serialize(format = 'json-ld', indent = 4).decode('utf-8'))
    # print()
    # return str(g.serialize(format='turtle').decode('utf-8'))
    return g


if __name__ == '__main__':
    main()
