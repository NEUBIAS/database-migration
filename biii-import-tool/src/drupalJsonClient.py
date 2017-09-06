import urllib3
import json

from urllib3 import ProxyManager

### initialialization of drupal URL + basic authentication +HTTP headers
# root_url = 'http://localhost:8888/drupal-8.2.4'

root_url = 'http://dev-bise2.pantheonsite.io'
# root_url = 'http://biii.eu'

http = urllib3.PoolManager()
# auth_header = urllib3.util.make_headers(basic_auth='admin:admin')
# migration:Mimimig!2020
# auth_header = urllib3.util.make_headers(basic_auth='perrine:P3rr1ne80!')
auth_header = urllib3.util.make_headers(basic_auth='migration:Mimimig2020')
http = ProxyManager("http://cache.ha.univ-nantes.fr:3128/", headers=auth_header)
http.headers.update(auth_header)
http.headers['Accept'] = 'application/json'
http.headers['Content-type'] = 'application/json'

### 1. create a simple GET query to retrieve a drupal node
req = http.request('GET', root_url + '/node/52?_format=json')
print(req.data.decode('utf-8'))
data = json.loads(req.data.decode('utf-8'))
print(json.dumps(data, indent=4, sort_keys=True))
print()

new_entry = {
    "title": [{"value": "Fiji_v50"}],
    "body": [{"value": "<p>Fiji V50</p>\r\n",
              "format": "basic_html", }],
    "field_has_author": [{"value": "An author"}],
    # "field_has_entry_curator": [{
    #        "target_id": 1,
    #        "target_type": "user",
    #        "target_uuid": "ff7211b9-a937-4c33-aac3-22aa10053480",
    #        "url": "/user/1"
    #    }
    # ],
    "field_has_entry_curator": [{
        "target_id": 1,
    }
    ],
    "field_is_dependent_of": [
        {
            "target_id": 51
        }
    ],
    "field_license_openness": [
        {
            "target_id": 3575
        }
    ],
    "field_supported_image_dimension": [
        {
            "target_id": 3561
        },
        {
            "target_id": 3562
        }
    ],
    "field_type": [
        {
            "target_id": 3567
        }
    ],
    "field_has_interaction_level": [
        {
            "target_id": 3573
        }
    ],
    "type": [{"target_id": "software"}]
}

floEntry = {
    # "nid":[{"value":2643}],
    "uuid": [{"value": "3c004d32-a6a3-45f3-a048-5eec23176378"}],
    "vid": [{"value": 2643}],
    "langcode": [{"value": "en"}],
    "type": [
        {"target_id": "software", "target_type": "node_type", "target_uuid": "54008715-4695-438a-9893-5da3c88d8f5d"}],
    "status": [{"value": True}],
    "title": [{"value": "SR-Tesseler-NEW"}],
    # "uid":[{"target_id":"587","target_type":"user","target_uuid":"d348ade6-a6cc-41c8-8395-90fbdf247d52", "url":"/user/587"}],
    "created": [{"value": 1468331651}],
    # "changed":[{"value":1468331651}],
    "promote": [{"value": True}],
    "sticky": [{"value": False}],
    # "revision_timestamp":[{"value":1468331651}],
    # "revision_uid":[{"target_id":"587","target_type":"user","target_uuid":"d348ade6-a6cc-41c8-8395-90fbdf247d52", "url":"/user/587"}],
    "revision_log": [{"value": "TO KEEP AS A TEST CASE"}],
    "revision_translation_affected": [{"value": True}],
    "default_langcode": [{"value": True}], "path": [], "synonyms": [],
    "body": [{
                 "value": "Localization-based super-resolution techniques open the door to unprecedented analysis of molecular organization. This task often involves complex image processing adapted to the specific topology and quality of the image to be analyzed.\n\nSR-Tesseler <bib>2661</bib> is an open-source segmentation software using Vorono<EF><BF><BD> tessellation constructed from the coordinates of localized molecules. It allows precise, robust and automatic quantification of protein organization at different scales, from the cellular level down to clusters of a few fluorescent markers.\n\nSR-Tesseler is insensitive to cell shape, molecular organization, background and noise, allowing comparing efficiently different biological conditions in a non-biased manner, and perform quantifications on various proteins and cell types.\n\nSR-Tesseler software comes with a very simple and intuitive graphical user interface, providing direct visual feedback of the results and is freely available under GPLv3 license.",
                 "format": "basic_html", "summary": ""}], "field_attribution_instructions": [],
    "field_free_tagging": [],
    # "field_give_feedback_on_this_soft":[{"status":2,"cid":0,"last_comment_timestamp":1468331651, "last_comment_name":"","last_comment_uid":587,"comment_count":0}],
    "field_has_author": [{"value": "Florian Levet, Jean-Baptiste Sibarita"}],
    "field_has_biological_terms": [],
    "field_has_comparison": [],
    "field_has_documentation": [],
    "field_has_doi": [{"value": "10.1038/nmeth.3579"}],
    # "field_has_entry_curator":[{"target_id":"587","target_type":"user","target_uuid":"d348ade6-a6cc-41c8-8395-90fbdf247d52", "url":"/user/587"}],
    "field_has_entry_curator": [{"target_id": "1"}],
    "field_has_function": [],
    "field_has_interaction_level": [
        {"target_id": "3574", "target_type": "taxonomy_term", "target_uuid": "51ad95cc-0d8c-4693-bde4-ba50c5fedf22",
         "url": "/taxonomy/term/3574"}],
    "field_has_license": [{"value": "GPLv3"}],
    "field_has_location": [
        {"uri": "http://www.iins.u-bordeaux.fr/team-sibarita-SR-Tesseler", "title": "", "options": []}],
    "field_has_programming_language": [
        {"target_id": "3593", "target_type": "taxonomy_term", "target_uuid": "a7b79b9f-2aa9-44aa-802d-0eb5bf7580ec",
         "url": "/taxonomy/term/3593"}],
    # "field_has_reference_publication":[{"uri":"10.1038/nmeth.3579","title":"","options":[]}],"field_has_topic":[],"field_has_usage_example":[],"field_image":[],"field_is_compatible_with":[],"field_is_covered_by_training_mat":[],"field_is_dependent_of":[],"field_license_openness":[{"target_id":"3575","target_type":"taxonomy_term","target_uuid":"56950dde-b53a-4ab4-b074-17c522559bb7", "url":"/taxonomy/term/3575"}],"field_platform":[{"target_id":"31","target_type":"taxonomy_term","target_uuid":"819d2357-7e78-48a4-be91-54cffe552307", "url":"/taxonomy/term/31"}],"field_supported_image_dimension":[],
    "field_has_reference_publication": [{"uri": "http://doi.org/10.1038/nmeth.3579", "title": "", "options": []}],
    "field_has_topic": [], "field_has_usage_example": [], "field_image": [], "field_is_compatible_with": [],
    "field_is_covered_by_training_mat": [], "field_is_dependent_of": [],
    "field_license_openness": [
        {"target_id": "3575", "target_type": "taxonomy_term", "target_uuid": "56950dde-b53a-4ab4-b074-17c522559bb7",
         "url": "/taxonomy/term/3575"}], "field_platform": [
        {"target_id": "31", "target_type": "taxonomy_term", "target_uuid": "819d2357-7e78-48a4-be91-54cffe552307",
         "url": "/taxonomy/term/31"}], "field_supported_image_dimension": [],
    "field_type": [
        {"target_id": "3567", "target_type": "taxonomy_term", "target_uuid": "c30819e9-32f2-4ad5-9e59-a8ec18c0ab62",
         "url": "/taxonomy/term/3567"}]}

### 2. create a POST query to insert a new drupal entry
# encoded_new_entry = json.dumps(new_entry).encode('utf-8')
encoded_new_entry = json.dumps(floEntry).encode('utf-8')

reqImport = http.request('POST', root_url + '/entity/node?_format=json', body=encoded_new_entry)
# reqImport = http.request('PATCH', root_url +'/node/59?_format=json', body=encoded_new_entry)
print(reqImport.reason)
res = json.loads(reqImport.data.decode('utf-8'))
print(json.dumps(res, indent=4, sort_keys=True))
print()
