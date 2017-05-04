#!/usr/bin/env python

import MySQLdb
import csv
import uuid

#Connection to the database of biii in drupal 8.x
dbDrupal8 = MySQLdb.connect(host='localhost', user='root', passwd='', db='drupal_bise2')
curBise8 = dbDrupal8.cursor()

#empty all the tables related to the taxonomy
s = "TRUNCATE taxonomy_term_data"
curBise8.execute(s)
s = "TRUNCATE taxonomy_term_field_data"
curBise8.execute(s)
s = "TRUNCATE taxonomy_term_hierarchy"
curBise8.execute(s)

#Import all txanomies that are not edam-bioimaging
cpt = 1
with open('D:/Biii/taxonomy_without_ontology.csv', 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
    next(csvfile)
    for row in spamreader:
        s = "INSERT INTO taxonomy_term_data (tid, vid, uuid, langcode) VALUES (%s, '%s', '%s', 'en')" % (row[0], row[1], uuid.uuid4())
        curBise8.execute(s)
        s = "INSERT INTO taxonomy_term_field_data (tid, vid, langcode, name, weight, changed, default_langcode) VALUES (%s, '%s', 'en', '%s', 0, 1493376256, 1)" % (row[0], row[1], row[2].replace("'", "\\'"))
        #print "%s" % s 
        curBise8.execute(s)
        s = "INSERT INTO taxonomy_term_hierarchy (tid, parent) VALUES (%s, 0)" % (row[0])
        curBise8.execute(s)
        cpt = cpt + 1
cpt = 3000
vidOperation = "edam_bioimaging_operation"
vidTopic = "edam_bioimaging_topic"
vidFormat = "edam_bioimaging_format"
vidData = "edam_bioimaging_data"
vidTags = "edam_bioimaging"
#Import the taxonomy related to edam-bioimaging. We directly create 4 vocabulaires related to operation, topic, data and format
with open('D:\Biii\EDAM-BIOIMAGING_corrected.csv', 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
    next(csvfile)
    for row in spamreader:
        tid_t = cpt
        uuid_t = row[0]
        name_t = row[1]
        vid_t = vidTags
        if "operation" in uuid_t.lower():
            vid_t = vidOperation
        if "topic" in uuid_t.lower():
            vid_t = vidTopic
        if "format" in uuid_t.lower():
            vid_t = vidFormat
        if "data" in uuid_t.lower():
            vid_t = vidData
        #print row
        s = "INSERT INTO taxonomy_term_data (tid, vid, uuid, langcode) VALUES (%s, '%s', '%s', 'en')" % (tid_t, vid_t, uuid_t)
        curBise8.execute(s)
        s = "INSERT INTO taxonomy_term_field_data (tid, vid, langcode, name, weight, changed, default_langcode) VALUES (%s, '%s', 'en', '%s', 0, 1493376256, 1)" % (tid_t, vid_t, name_t)
        #print "%s" % s
        curBise8.execute(s)
        cpt = cpt + 1
#update of the hierarchy table
with open('D:\Biii\EDAM-BIOIMAGING_corrected.csv', 'rb') as csvfile:
    cpt = 3000
    spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
    next(csvfile)
    for row in spamreader:
        if cpt > 0:
            #print ', '.join(row)
            parentUuid = row[7]#row[3]
            t1 = parentUuid.find("|")
            if t1 != -1:
                parentUuid = parentUuid[0:t1]
            if parentUuid:
                #For now, we cannot deal with multiple inheritance, which is separated by a | in the bioEdam csv file
                #Solution is to keep only the first parent
                if(not "owl" in parentUuid):
                    s = "SELECT ttdc.tid FROM taxonomy_term_data ttdc WHERE ttdc.uuid = '%s'" % parentUuid
                    curBise8.execute(s)
                    parent = curBise8.fetchone()
                    if parent:
                        s = "INSERT INTO taxonomy_term_hierarchy (tid, parent) VALUES (%s, %s)" % (cpt, parent[0])
                        curBise8.execute(s)
                    else:
                        s = "SELECT ttdc.tid, ttdc.name FROM taxonomy_term_field_data ttdc WHERE ttdc.tid = '%s'" % cpt
                        curBise8.execute(s)
                        res = curBise8.fetchone()
                        #print res
                        print "There is a problem with the finding of the parent %s" % parentUuid
                else:
                    s = "SELECT ttdc.tid, ttdc.name FROM taxonomy_term_field_data ttdc WHERE ttdc.tid = '%s'" % cpt
                    curBise8.execute(s)
                    res = curBise8.fetchone()
                    print res
                    s = "INSERT INTO taxonomy_term_hierarchy (tid, parent) VALUES (%s, 0)" % (cpt)
                    curBise8.execute(s)
        cpt = cpt + 1

dbDrupal8.commit()
