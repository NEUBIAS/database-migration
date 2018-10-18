# Process to update the EDAM BioImaging taxonomy
This updating is done with the use of one python scripts. 

### biseEU\_importer\_taxonomy.py

Prerequesite: creation of a View in Drupal that expose the taxonomy terms

- Login as administrator in Biii.eu
- Go to Structure, then Views
- Click on the Add view button
- Define a name for the view (for instance "taxonomy view")
- In "View settings", choose "Taxonomy terms" from the Show list
- Check "Create a page"
- For "Display format" choose "HTML List" of "Fields"
- Check "Provide a REST export"
- Provide a "REST export path" such as "taxo" for instance
- Click on "Save and edit"
- Add taxonomy terms that you want to expose by clicking on the "Add" button in the "Fields" category
- Choose "Term ID" and "UUID" for instance
- Click on "Apply (all displays)" twice
- Click on the "Add" button of the "Sort criteria" category
- Choose the "Term ID", click on "Apply (all displays)" twice
- To display all the terms in the same window, click on "Mini" in the "Pager" category
- Check the "Display all items" then click on "Apply (all displays)"
- Click on "Apply"
- Click on "Save"
- Go to the address [http://biii.eu/taxonomy-view](http://biii.eu/taxonomy-view), all the taxonomy terms with the tid, name and uuid are displayed, in ascending order on the tid

With this view, we still lack the hierarchy information since we don't have acces to the parent ID. This relation can be added to the View

-  In the "page" section of the View, click on "Advanced"
-  Click on the "Add" button of the "Relationships" category
-  Check "Parent term" and click on "Apply (all displays)"
-  Uncheck "Require this relationship", then click on "Apply (all displays)"
-  Click on the "Add" button of the "Fields" category
-  Check "Term ID" and click on "Apply (all displays)"
-  Choose "Parent" in the "Relationship" list then click on "Apply (all displays)"
-  Click on "Save"
-  Go to the address [http://biii.eu/taxonomy-view](http://biii.eu/taxonomy-view), the parent ID has been added if it exists
-  Don't forget to go to the "REST export" page. Change "Authentification" to "basic_auth" and "user". Change "Show" to "Fields". Do the same process as for the "Page" page on the "Fields" to display, "Sort criteria" and "Pager". Click on "Taxonomy term: Name" from the "Fields" category and uncheck "Link to Taxonomy term". Name, in "PATH SETTINGS", the Path as "/taxo".

Run the biseEU\_importer\_taxonomy.py with the parameters shown in the script
Thes script will open the "EDAM-bioimaging_xxx.tsv" file to read each term of the EDAM bioimaging taxonomy. Then it will compare those with the taxonomy exposed with the taxo view. Taxonomy terms with new description and/or synonyms will be updated. Taxonomy terms that do not exist will be created.

Command line :
python.exe biseEU_importer_taxonomy.py -u username -p xxx -td url_to_website -i EDAM-bioimaging.tsv

The url_to_website parameter can be obtained by using the command "lando info". I gives several info with these two of interests :

    "urls":[
    	"https://localhost:32776",
        "http://localhost:32777",
        "http://bisescratch.lndo.site",
        "https://bisescratch.lndo.site"
    ]

	and

	"external_connection": {
      "host": "localhost",
      "port": "32778"
    }

url_to_website should be replaced by http://localhost:32777 (check that the port is the same for you)

Then the line 92 of biseEU_importer_taxonomy.py may need to be replaced with the port of the external_connection

    dbBise2_dev = MySQLdb.connect(host='localhost', port=32778,  user='drupal8', passwd='drupal8', db='drupal8')
