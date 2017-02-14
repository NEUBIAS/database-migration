#!/usr/bin/env python

import os
import MySQLdb

host = os.environ.get("MYSQL_HOST", "127.0.0.1")
passwd = os.environ.get("MYSQL_PASS", "pass")

#Creation of the datamodel for bise independant of any cms
dbPerso = MySQLdb.connect(host=host, user='root', passwd=passwd)
curPerso = dbPerso.cursor()
#Test if db_biii_perso exists, if yes drop the complete database
sql = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'db_biii_perso'"
curPerso.execute(sql)
exist = curPerso.fetchone()
if(exist):
    sql = 'DROP DATABASE db_biii_perso'
    curPerso.execute(sql)
sql = 'CREATE DATABASE db_biii_perso'
curPerso.execute(sql)
sql = 'ALTER DATABASE db_biii_perso CHARACTER SET utf8 COLLATE utf8_general_ci'
curPerso.execute(sql)
dbPerso = MySQLdb.connect(host=host, user='root', passwd=passwd, db='db_biii_perso')
curPerso = dbPerso.cursor()
with open('creationTablesSQL_good.txt', 'r') as myfile:
    sql = myfile.read()
curPerso.execute(sql)
curPerso.close()
curPerso = dbPerso.cursor()

#Connection to the database of biii in drupal 7.x
dbDrupal = MySQLdb.connect(host=host, user='root', passwd=passwd, db='drupal_biii')
cur = dbDrupal.cursor()
#Get all authors
cur.execute("SELECT bcd.cid, bcd.name, bcd.affiliation FROM biblio_contributor_data bcd")
for author in cur.fetchall():
    s = "INSERT INTO Authors (id_author, Complete_name, Affiliation) VALUES (%s, '%s', '%s')" % (author[0], author[1], author[2])
    curPerso.execute(s)
#Get all author-paper relations
cur.execute("SELECT bc.cid, bc.vid, bc.rank FROM biblio_contributor bc")
for ap_relation in cur.fetchall():
    s = "INSERT INTO AuthorPaperRelation (id_author, id_paper, Position) VALUES (%s, %s, '%s')" % (ap_relation[0], ap_relation[1], ap_relation[2])
    curPerso.execute(s)
#Get all keywords
cur.execute("SELECT bkd.kid, bkd.word FROM biblio_keyword_data bkd")
for keyword in cur.fetchall():
    s = "INSERT INTO Keywords (id_keyword, Name) VALUES (%s, '%s')" % (keyword[0], keyword[1])
    curPerso.execute(s)
#Get all keyword-paper relations
cur.execute("SELECT bk.kid, bk.vid FROM biblio_keyword bk")
for kp_relation in cur.fetchall():
    s = "INSERT INTO KeywordPaperRelation (id_keyword, id_paper) VALUES (%s, %s)" % (kp_relation[0], kp_relation[1])
    curPerso.execute(s)
#Get all biblio types
cur.execute("SELECT bt.tid, bt.name FROM biblio_types bt")
for btypes in cur.fetchall():
    s = "INSERT INTO BiblioType (id_type, Name) VALUES (%s, '%s')" % (btypes[0], btypes[1])
    curPerso.execute(s)
#Get all biblio
cur.execute("SELECT b.vid FROM biblio b")
id_biblios = cur.fetchall()
for id_biblio in id_biblios:
    s = "SELECT biblio_type, biblio_sort_title, biblio_secondary_title, biblio_volume, biblio_pages, biblio_year, biblio_issn, biblio_doi, biblio_abst_e, biblio_date, biblio_url, biblio_isbn, biblio_issue FROM biblio b WHERE b.vid = %s" % (id_biblio[0])
    cur.execute(s)
    info = cur.fetchone()
    s = "INSERT INTO AcademicPaper (id_paper, id_type, Title, Journal, Volume, Pages, Year, ISSN, doi, Abstract, Date, URL, ISBN, Issue) VALUES (%s, %s, '%s', '%s', '%s', '%s', %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (id_biblio[0], info[0], info[1], info[2].replace("'", "\\'"), info[3], info[4], info[5], info[6], info[7], info[8].replace("'", "\\'"), info[9], info[10], info[11], info[12])
    curPerso.execute(s)

#Creation of the TypeSoftware table values
s = "INSERT INTO TypeSoftware (id_type, Name) VALUES (0, 'Unknown')"
curPerso.execute(s)
s = "INSERT INTO TypeSoftware (id_type, Name) VALUES (1, 'API')"
curPerso.execute(s)
s = "INSERT INTO TypeSoftware (id_type, Name) VALUES (2, 'Application')"
curPerso.execute(s)
s = "INSERT INTO TypeSoftware (id_type, Name) VALUES (3, 'Plugin')"
curPerso.execute(s)

#Creation of the OS table values
all_os = [(0, 'Unknown'), (1, 'Windows'), (2, 'Linux'), (3, 'Mac OS X'), (4, 'FreeBSD'), (5, 'MATLAB'), (6, 'Web'), (7, 'iOS'), (8, 'Fedora'), (9, 'ImageJ'), (10, 'FIJI')]
for i in range(len(all_os)):
    s = "INSERT INTO OS (id_os, Name) VALUES (%s, '%s')" % (all_os[i][0], all_os[i][1])
    curPerso.execute(s)

#Feed the SoftwareOSRelation table
winS = 'win'
macS = 'os'
linuxS = 'lin'
pcS = 'pc'
allS = 'all'
anyS = 'any'
multiS = 'multiplatform'
cur.execute("SELECT f.entity_id, f.field_platform_value FROM field_data_field_platform f")
for os in cur.fetchall():
    value_os = os[1].replace("'", "\\'")
    if winS in value_os.lower() or pcS in value_os.lower():
        s = "INSERT INTO SoftwareOSRelation (id_os, id_software) VALUES (%s, 1)" % os[0]
        curPerso.execute(s)
    if linuxS in value_os.lower():
        s = "INSERT INTO SoftwareOSRelation (id_os, id_software) VALUES (%s, 2)" % os[0]
        curPerso.execute(s)
    if macS in value_os.lower():
        s = "INSERT INTO SoftwareOSRelation (id_os, id_software) VALUES (%s, 3)" % os[0]
        curPerso.execute(s)
    for i in range(4, len(all_os)):
        if all_os[i][1].lower() in value_os.lower():
            s = "INSERT INTO SoftwareOSRelation (id_os, id_software) VALUES (%s, %s)" % (os[0], i)
            curPerso.execute(s)
    if allS in value_os.lower() or anyS in value_os.lower() or multiS in value_os.lower():
        s = "INSERT INTO SoftwareOSRelation (id_os, id_software) VALUES (%s, 1)" % os[0]
        curPerso.execute(s)
        s = "INSERT INTO SoftwareOSRelation (id_os, id_software) VALUES (%s, 2)" % os[0]
        curPerso.execute(s)
        s = "INSERT INTO SoftwareOSRelation (id_os, id_software) VALUES (%s, 3)" % os[0]
        curPerso.execute(s)
     #print ("%s, '%s'") % (os[0], os[1].replace("'", "\\'"))

#Get all taxonomy/entity relations
cur.execute("SELECT ti.tid, ti.nid FROM taxonomy_index ti")
for te_relation in cur.fetchall():
    s = "INSERT INTO TagEntityRelation (id_tag, id_entity) VALUES (%s, %s)" % (te_relation[0], te_relation[1])
    curPerso.execute(s)
#Get all taxonomy terms
cur.execute("SELECT ttd.tid, ttd.name FROM taxonomy_term_data ttd")
for tag in cur.fetchall():
    s = "INSERT INTO Tags (id_tag, Name) VALUES (%s, '%s')" % (tag[0], tag[1].replace("'", "\\'"))
    curPerso.execute(s)

#Get all user skills
cur.execute("SELECT f.entity_id, f.field_target_audience_value FROM field_data_field_target_audience f")
for userSkill in cur.fetchall():
    s = "INSERT INTO UserSkill (id_user_skill, Skill) VALUES (%s, '%s')" % (userSkill[0], userSkill[1].replace("'", "\\'"))
    curPerso.execute(s)

#Get all OS
#cur.execute("SELECT f.entity_id, f.field_platform_value FROM field_data_field_platform f")
#for os in cur.fetchall():
#    s = "INSERT INTO OS (id_os, Name) VALUES (%s, '%s')" % (os[0], os[1].replace("'", "\\'"))
#    curPerso.execute(s)
#    print ("%s, '%s'") % (os[0], os[1].replace("'", "\\'"))

#Get all users
cur.execute("SELECT u.uid, u.name FROM users u")
users = cur.fetchall()
for user in users:
    cur.execute("SELECT f.field_myurl_value FROM field_data_field_myurl f WHERE f.entity_id = %s" % user[0])
    res = cur.fetchone()
    s = "INSERT INTO User (id_user, Name, url) VALUES (%s, '%s', " % (user[0], user[1].replace("'", "\\'"))
    if(res):
        s += ("'%s')" % res[0])
    else:
        s += "NULL)"
    curPerso.execute(s)

nbWorkflow = nbProcess = nbLanguage = 1
#Get all the nodes
cur.execute("SELECT n.nid FROM node n")# WHERE n.nid = 2643 OR n.nid = 2440")
id_nodes = cur.fetchall()
nb_nodes = len(id_nodes)
max_id_node = 0
icy_script_id = 0
for id_node in id_nodes:
    if (id_node[0] > max_id_node):
        max_id_node = id_node[0]
    s = "SELECT n.nid, n.uid, n.type, n.title, n.vid FROM node n WHERE n.nid = %s" % id_node
    cur.execute(s)
    res = cur.fetchone()
    id_entity = res[0]
    id_curator = res[1]
    typeNode = res[2]
    title = res[3].replace("'", "\\'")
    id_revision = res[4]
    body = authors = id_user_skill = id_paper = locationPath = None
    s = "SELECT field_target_audience_value FROM field_data_field_target_audience f WHERE f.entity_id = %s" % id_entity
    cur.execute(s)
    res = cur.fetchone()
    if(res):
        id_user_skill = id_entity
    s = "SELECT body_value FROM field_data_body f WHERE f.entity_id = %s" % id_entity
    cur.execute(s)
    res = cur.fetchone()
    if(res):
        body = res[0].replace("'", "\\'")

    #Authors
    if(typeNode == 'function' or typeNode == 'software_package' or typeNode == 'languages'):
        s = "SELECT field_author_s__value FROM field_data_field_author_s_ f WHERE f.entity_id = %s" % id_entity
        cur.execute(s)
        res = cur.fetchone()
        if(res):
            authors = res[0].replace("'", "\\'")
    elif(typeNode == 'workflows'):
        s = "SELECT field_workflow_author_value FROM field_data_field_workflow_author f WHERE f.entity_id = %s" % id_entity
        cur.execute(s)
        res = cur.fetchone()
        if(res):
            authors = res[0].replace("'", "\\'")

    #URL
    if(typeNode == 'function'):
        s = "SELECT field_url_value FROM field_data_field_url f WHERE f.entity_id = %s" % id_entity
        cur.execute(s)
        res = cur.fetchone()
        if(res):
            locationPath = res[0].replace("'", "\\'")
        else:
            s = "SELECT field_url_func_value FROM field_data_field_url_func f WHERE f.entity_id = %s" % id_entity
            cur.execute(s)
            res = cur.fetchone()
            if(res):
                locationPath = res[0].replace("'", "\\'")
    elif(typeNode == 'languages'):
        s = "SELECT field_url_link_value FROM field_data_field_url_link f WHERE f.entity_id = %s" % id_entity
        cur.execute(s)
        res = cur.fetchone()
        if(res):
            locationPath = res[0].replace("'", "\\'")
    elif(typeNode == 'software_package' or typeNode == 'training'):
        s = "SELECT field_link_value FROM field_data_field_link f WHERE f.entity_id = %s" % id_entity
        cur.execute(s)
        res = cur.fetchone()
        if(res):
            locationPath = res[0].replace("'", "\\'")
    s = "INSERT INTO Entity (id_entity, id_curator, Title, id_user_skill, id_paper, Body, Authors, LocationPath) VALUES (%s, %s, '%s', " % (id_entity, id_curator, title)
    if(id_user_skill == None):
        s += "NULL, "
    else:
        s += ("%s, " % id_user_skill)
    if(id_paper == None):
        s += "NULL, "
    else:
        s += ("%s, " % id_paper)
    if(body == None):
        s += "NULL, "
    else:
        s += ("'%s', " % body)
    if(authors == None):
        s += "NULL, "
    else:
        s += ("'%s', " % authors)
    if(locationPath == None):
        s += "NULL)"
    else:
        s += ("'%s')" % locationPath)
    #print ("%s") % s
    curPerso.execute(s)
    if (typeNode == 'languages'):
        if (not 'Icy' in title or title == 'Icy Script'):
            s = "INSERT INTO ProgrammingLanguage (id_language, id_entity) VALUES (%s, %s)" % (nbLanguage, id_entity)
            curPerso.execute(s)
            print ("%s is a language, %s") % (title, id_entity)
            if(title == 'Icy Script'):
               icy_script_id = nbLanguage
            nbLanguage = nbLanguage + 1

#Insert the missing programming languages
max_id_node = max_id_node + 1
s = "INSERT INTO Entity (id_entity, id_curator, Title, Body) VALUES (%s, 587, 'SQL', 'SQL (Structured Query Language) is a special-purpose domain-specific language used in programming and designed for managing data held in a relational database management system (RDBMS), or for stream processing in a relational data stream management system (RDSMS).')" % max_id_node
curPerso.execute(s)
s = "INSERT INTO ProgrammingLanguage (id_language, id_entity) VALUES (%s, %s)" % (nbLanguage, max_id_node)
curPerso.execute(s)
max_id_node = max_id_node + 1
nbLanguage = nbLanguage + 1
s = "INSERT INTO Entity (id_entity, id_curator, Title, Body) VALUES (%s, 587, 'FORTRAN', 'Fortran (formerly FORTRAN, derived from \\'Formula Translation\\') is a general-purpose, imperative programming language that is especially suited to numeric computation and scientific computing. Originally developed by IBM in the 1950s for scientific and engineering applications, Fortran came to dominate this area of programming early on and has been in continuous use for over half a century in computationally intensive areas such as numerical weather prediction, finite element analysis, computational fluid dynamics, computational physics, crystallography and computational chemistry. It is a popular language for high-performance computing and is used for programs that benchmark and rank the world\\'s fastest supercomputers.')" % max_id_node
curPerso.execute(s)
s = "INSERT INTO ProgrammingLanguage (id_language, id_entity) VALUES (%s, %s)" % (nbLanguage, max_id_node)
curPerso.execute(s)
max_id_node = max_id_node + 1
nbLanguage = nbLanguage + 1
s = "INSERT INTO Entity (id_entity, id_curator, Title, Body) VALUES (%s, 587, 'PHP', 'PHP is a server-side scripting language designed primarily for web development but also used as a general-purpose programming language.')" % max_id_node
curPerso.execute(s)
s = "INSERT INTO ProgrammingLanguage (id_language, id_entity) VALUES (%s, %s)" % (nbLanguage, max_id_node)
curPerso.execute(s)
max_id_node = max_id_node + 1
nbLanguage = nbLanguage + 1

s = "SELECT pl.id_language, e.Title FROM ProgrammingLanguage pl, Entity e WHERE pl.id_entity = e.id_entity"
curPerso.execute(s)
all_languages = curPerso.fetchall()
for langs in all_languages:
    print (' '.join("%s" % info for info in langs))
#test all languages (juste the first word) of the title wrt all ecosystem values, if works add the relation in the softwarelanguagerelation

#table 'field_data_field_type' for software -> gives the type of the software: library, application etc.

nbSoftware = 1
s = "SELECT n.nid, n.type, n.title FROM node n"
cur.execute(s)
for node in cur.fetchall():
    if (node[1] == 'software_package'):
        s = "INSERT INTO SoftwareArtifact (id_software, id_entity) VALUES (%s, %s)" % (nbSoftware, node[0])
        curPerso.execute(s)
        s = "SELECT f.field_ecosystem_value FROM field_data_field_ecosystem f, node n WHERE f.entity_id = %s AND n.nid = %s" % (node[0], node[0])
        cur.execute(s)
        ecoS = cur.fetchone()
        if ecoS:
            print ("%s | %s | %s") % (ecoS[0], node[2], node[0])
            tmp = ecoS[0].replace(' /', ',')
            tmp = tmp.replace('/', ', ')
            listOld = tmp.split(', ')
            for old in listOld:
                for langs in all_languages:
                    lang = langs[1].split(' ')[0]
                    if(lang.lower() == old.lower()):
                        s = "INSERT INTO SoftwareLanguageRelation (id_software, id_language) VALUES (%s, %s)" % (nbSoftware, langs[0])
                        curPerso.execute(s)
                        s = "INSERT INTO SoftwareLanguageRelation (id_software, id_language) VALUES (%s, %s) -> %s" % (nbSoftware, langs[0], langs[1])
                        #print ("%s") % s
        else:
            print "No ecosystem, %s | %s" % (node[2], node[0])
        nbSoftware = nbSoftware + 1

#Create the process table
nbProcess = 1
s = "SELECT n.nid, n.type FROM node n"
cur.execute(s)
for node in cur.fetchall():
    if(node[1] == 'function'):
        s = "INSERT INTO Process (id_process, id_entity) VALUES (%s, %s)" % (nbProcess, node[0])
        #print ("%s") % s
        curPerso.execute(s)
        nbProcess = nbProcess + 1

#Create the softwareProcessRelation
s = "SELECT f.entity_id, f.field_package_library_target_id FROM field_data_field_package_library f"
cur.execute(s)
for link in cur.fetchall():
    s = "SELECT p.id_process, s.id_software FROM Process p, SoftwareArtifact s WHERE p.id_entity = %s AND s.id_entity = %s" % (link[0], link[1])
    curPerso.execute(s)
    res = curPerso.fetchone()
    if res:
        s = "INSERT INTO SoftwareProcessRelation (id_software, id_process) VALUES (%s, %s)" % (res[1], res[0])
        curPerso.execute(s)
    else:
        print "softwareProcessRelation - Not working for %s and %s" % (link[0], link[1])

#Create the workflow table
nbWorkflow = 1
s = "SELECT n.nid, n.type FROM node n"
cur.execute(s)
for node in cur.fetchall():
    if(node[1] == 'workflows'):
        s = "INSERT INTO Workflow (id_workflow, id_entity) VALUES (%s, %s)" % (nbWorkflow, node[0])
        #print ("%s") % s
        curPerso.execute(s)
        nbWorkflow = nbWorkflow + 1

#Create the softwareWorkflowRelation
s = "SELECT f.entity_id, f.field_package_library_wf_target_id, f.delta FROM field_data_field_package_library_wf f"
cur.execute(s)
for link in cur.fetchall():
    s = "SELECT w.id_workflow, s.id_software FROM Workflow w, SoftwareArtifact s WHERE w.id_entity = %s AND s.id_entity = %s" % (link[0], link[1])
    curPerso.execute(s)
    res = curPerso.fetchone()
    if res:
        s = "INSERT INTO SoftwareWorkflowRelation (id_software, id_workflow, Position) VALUES (%s, %s, %s)" % (res[1], res[0], link[2])
        curPerso.execute(s)
    else:
        print "softwareWorkflowRelation - Not working for %s and %s" % (link[0], link[1])

#Create the WorkflowLanguageRelation
s = "SELECT f.entity_id, f.field_language_target_id, f.delta, n.title FROM field_data_field_language f, node n WHERE f.field_language_target_id = n.nid"
cur.execute(s)
for link in cur.fetchall():
    s = "SELECT w.id_workflow, l.id_language FROM Workflow w, ProgrammingLanguage l WHERE w.id_entity = %s AND l.id_entity = %s" % (link[0], link[1])
    curPerso.execute(s)
    res = curPerso.fetchone()
    if res:
        s = "INSERT INTO WorkflowLanguageRelation (id_language, id_workflow, Position) VALUES (%s, %s, %s)" % (res[1], res[0], link[2])
        curPerso.execute(s)
    elif 'icy' in link[3].lower():
        s = "SELECT w.id_workflow FROM Workflow w WHERE w.id_entity = %s" % link[0]
        curPerso.execute(s)
        res = curPerso.fetchone()
        s = "INSERT INTO WorkflowLanguageRelation (id_language, id_workflow, Position) VALUES (%s, %s, %s)" % (icy_script_id, res[0], link[2])
        curPerso.execute(s)
    else:
        print "WorkflowLanguageRelation - Not working for %s and %s" % (link[0], link[1])

#Create the WorkflowProcessRelation
s = "SELECT f.entity_id, f.field_workflow_target_id, f.delta FROM field_data_field_workflow f"
cur.execute(s)
for link in cur.fetchall():
    s = "SELECT w.id_workflow, p.id_process FROM Workflow w, Process p WHERE w.id_entity = %s AND p.id_entity = %s" % (link[1], link[0])
    curPerso.execute(s)
    res = curPerso.fetchone()
    if res:
        s = "INSERT INTO WorkflowProcessRelation (id_process, id_workflow, Position) VALUES (%s, %s, %s)" % (res[1], res[0], link[2])
        curPerso.execute(s)
    else:
        s = "SELECT s.id_software, p.id_process FROM SoftwareArtifact s, Process p WHERE s.id_entity = %s AND p.id_entity = %s" % (link[1], link[0])
        curPerso.execute(s)
        res = curPerso.fetchone()
        if res:
            s = "INSERT INTO SoftwareProcessRelation (id_process, id_software) VALUES (%s, %s)" % (res[1], res[0])
            curPerso.execute(s)
        else:
            print "WorkflowProcessRelation - Not working for %s and %s" % (link[0], link[1])

print (nb_nodes)

#s = "mysqldump --databases  db_biii_perso > tmp.sql"
#cur.execute(s)

#Quid de l'ecosystem pour les software artifacts (entity ?)

#print ("%s") % sql
