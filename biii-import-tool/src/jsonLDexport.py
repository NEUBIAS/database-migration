import urllib3
import json
from rdflib import Graph

#/Users/gaignard-a/Documents/Dev/neubias-data-model/data-dumps

#http = urllib3.PoolManager()
http = urllib3.ProxyManager("http://cache.ha.univ-nantes.fr:3128/")

#auth_header = urllib3.util.make_headers(basic_auth='admin:admin')
#http.headers.update(auth_header)
http.headers['Accept']='application/json'
http.headers['Content-type']='application/json'

r = http.request('GET', 'http://biii.eu/node?_format=json')
d = json.loads(r.data.decode('utf-8'))

### 1. create a simple GET query to retrieve a drupal node
req = http.request('GET', 'http://biii.eu/node/38?_format=json')
data = json.loads(req.data.decode('utf-8'))
#print(json.dumps(data, indent=4, sort_keys=True))
#print()

entry = data

ctx = {
    "@context": {
        "@base": "http://biii.eu/node/",
        "neubias": "http://neubias/",
        "dc": "http://dcterms/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",

        "field_has_reference_publication": "neubias:has_publi",
        "hasDescription": "rdfs:comment",
        "hasTitle": "dc:title",
        "hasSupportedDimension": "neubias:has_supported_image_dimension",
        "hasRunningPlatform": "neubias:has_running_platform"
    }
}
entry["@id"] = str(entry["nid"][0]["value"])
entry["@type"] = str(entry["type"][0]["target_id"])
entry.update(ctx)

entry["hasDescription"] = entry["body"][0]["value"]

entry["hasTitle"] = entry["title"][0]["value"]

for item in entry["field_supported_image_dimension"]:
    if "hasSupportedDimension" in entry:
        entry["hasSupportedDimension"].append(item["target_id"])
    else:
        entry["hasSupportedDimension"] = [item["target_id"]]

for item in entry["field_platform"]:
    if "hasRunningPlatform" in entry:
        entry["hasRunningPlatform"].append(item["target_id"])
    else:
        entry["hasRunningPlatform"] = [item["target_id"]]

#print(json.dumps(entry, indent=4, sort_keys=True))
#print()

raw_jld = json.dumps(entry)
g = Graph().parse(data=raw_jld, format='json-ld')
print(g.serialize(format='turtle').decode('utf-8'))