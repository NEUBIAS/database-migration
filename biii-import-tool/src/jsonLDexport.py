import urllib3
import json
from src.biseEU_importer import get_web_service


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


def rdfize(json_entry):

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
            "requires": "nb:requires"
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
        # print(item)
        entry["hasAuthor"] = item["value"]

    # for item in entry['field_has_entry_curator']:
        # print(item)

    for item in entry['field_has_function']:
        # print(item)
        if not "hasFunction" in entry.keys():
            entry["hasFunction"] = [{"@id": item["target_uuid"]}]
        else:
            entry["hasFunction"].append({"@id": item["target_uuid"]})

    for item in entry['field_has_topic']:
        # print(item)
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