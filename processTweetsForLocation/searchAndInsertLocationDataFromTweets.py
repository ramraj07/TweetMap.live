#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 17:11:27 2017

@author: ramrajvelmurugan
"""


import psycopg2
import pandas as pd
import os

import sys
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

username = 'postgres'
password = os.environ['db_password']
db = 'tweets_db'

engine = create_engine('postgres://%s:%s@104.154.139.71/%s'%(username,password,db))
connection = engine.connect()
Base = declarative_base()
Base.metadata.reflect(engine)
Base.metadata.tables.keys()
neighborhoods = pd.read_sql_query("""

    select id,tags from 
    planet_osm_nodes where 'neighbourhood' = any(tags)
    OR 'suburb' = any(tags);


""",engine)
neighborhoodsWithNames = neighborhoods[
    neighborhoods.tags.astype(str).str.contains("name")]
nn = len(neighborhoodsWithNames)
for ind,neighborhood in neighborhoodsWithNames.iterrows():
    name = neighborhood.tags[neighborhood.tags.index("name")+1]
    id = neighborhood.id
    searchresults = pd.read_sql_query("""
    
        SELECT tweet_id FROM 
        tweets WHERE 
        document @@ phraseto_tsquery(%(name)s) limit 10;
    
    """,engine,params={"name":name})
    for ind,searchresult in searchresults.iterrows():
        insertvalues = {
            "tweet_id":int(searchresult.tweet_id),
            "osm_id":int(id)}
        sqlquery ="INSERT INTO osmTweetLocalization(tweet_id,osm_id) VALUES("+str(searchresult.tweet_id)+","+str(id)+") ON CONFLICT DO NOTHING;"
        result = connection.execute(sqlquery)
        
    print(  str(ind)+
            " of "+ 
            str(len(nn))+": Found and recorded "+str(len(searchresults))+" tweets for "+name)
