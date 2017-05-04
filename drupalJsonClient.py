import urllib3
import json

### initialialization of drupal URL + basic authentication +HTTP headers
root_url = 'http://localhost:8888/drupal-8.2.4'
http = urllib3.PoolManager()
auth_header = urllib3.util.make_headers(basic_auth='admin:admin')
http.headers.update(auth_header)
http.headers['Accept']='application/json'
http.headers['Content-type']='application/json'

### 1. create a simple GET query to retrieve a drupal node
req = http.request('GET', root_url+'/node/4?_format=json')
data = json.loads(req.data.decode('utf-8'))
print(json.dumps(data, indent=4, sort_keys=True))
print()


### 2. create a POST query to insert a new drupal entry
new_entry= {
    "title": [{"value": "Fiji_v5"}],
    "body": [{"value": "<p>Fiji V5 bla bla </p>\r\n",
              "format": "basic_html",}],
    "field_has_ontology_tag": [{"target_id": "2"}],
    "type": [{"target_id": "software"}]
}
encoded_new_entry = json.dumps(new_entry).encode('utf-8')

reqImport = http.request('POST', root_url +'/entity/node?_format=json', body=encoded_new_entry)
print(reqImport.reason)
res=json.loads(reqImport.data.decode('utf-8'))
print(json.dumps(res, indent=4, sort_keys=True))
print()