# Database migration
This repository hosts migration scripts and sample intermediate data. 

### Migration workflow
1. Extraction of http://biii.upf.edu database
2. Conversion of biii DB entries into JSON files
3. HTTP POST of JSON files into the new Drupal site through its REST API -> http://dev-bise2.pantheonsite.io

### Tooling
