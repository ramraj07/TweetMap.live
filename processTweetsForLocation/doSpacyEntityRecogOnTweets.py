#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script uses the Spacy NLP package to perform Entity recognition on
each tweet (only once, using a boolean "flag" column to keep track) and 
finds all entities of type ORG, LOC or GPE. Then it inserts these results
(with the tweet_id reference) into another table spacyentities01 for
further use by other scripts and models. 

Created on Tue Sep 19 18:21:57 2017

@author: ramrajvelmurugan
"""

import spacy
import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

import sys
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

username = 'postgres'
password = os.environ['db_password']
database = 'tweets_db'
engine = create_engine('postgres://%s:%s@104.154.139.71/%s'%(username,password,database))
connection = engine.connect()

# do 1000s of tweets at a time to minimize database read write numbers
nTweetsAtATime = 1000

# we use this flag to make sure we have at least 1 tweet left to search through 
# in each iteration of the while loop below 
atleastonetweet = True

nlp = spacy.load('en_default')

while atleastonetweet:
    # This SQL query loads n tweets that which have not 
    # been processed by this script yet, and are supposed 
    # to be in english (based on the user's detail)
    df = pd.read_sql_query(
        """
        begin; 
        select 
            tweet_id,tweet_text 
        from tweets 
        join users 
        on tweets.user_id = users.id 
        where 
            spacyentitysearch01 is false 
        and lower(lang) like 'en%%' 
        limit  %(nTweets)s 
        for update skip locked;""", 
        params = {"nTweets":nTweetsAtATime},
        engine)
        
    # the following logic generates two SQL statements, an insert statement for each entity
    # name of type ORG, LOC or GPE (380,381 and 382 codes) in the spacyentities01 table 
    # and a flag that says the tweet has been analyzed, and commits them in the end as a 
    # transaction. 
    sqlstring = u'insert into spacyentities01 (tweet_id,entityname,entity_type_id) values '
    sqlstring2 = 'update tweets set spacyentitysearch01=true where tweet_id in ('
    atleast1entity=False
    atleastonetweet = False
    entitycount=0
    for _,tweet in df.iterrows():
        doc = nlp(tweet.tweet_text)
        sqlstring2=sqlstring2+str(tweet.tweet_id)+','
        atleastonetweet=True 
        for ent in doc.ents:
            if ent.label in (380,381,382):
                sqlstring=sqlstring+"("+str(tweet.tweet_id)+",'"+ent.text.translate(str.maketrans({"'":None}))+"',"+str(ent.label)+"),"
                atleast1entity = True
                entitycount=entitycount+1
    if atleastonetweet:
        if atleast1entity:
            finalsql= sqlstring2[:-1]+"); "+sqlstring[:-1]+"; commit;"
        else:
            finalsql=sqlstring2[:-1]+"); "+"; commit;"
    else:
        finalsql="commit;"
    result = connection.execute(finalsql)
    print('Found '+str(entitycount)+' entities in '+str(nTweetsAtATime)+' tweets.')