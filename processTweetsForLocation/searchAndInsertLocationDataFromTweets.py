#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

This script reads all the nodes in the postgres table plane_osm_nodes 
(which was created first by using osm2psql tool alongwith the OSM dump
for the state of Florida) that have a name tag (which is not a bus_stop)
and does a full text search on all the tweets (using the already prepared 
'document' field which contains the full text search index for the tweet_text
field) and inputs an entry for each combination of tweet_id and osm_id that
match into the osmTweetLocalization table. This table has a unique tweet_id,
osm_id combination criteria, so each combination will only be entered once
and hence this script can be run repeatedly without worrying about duplicating
data (though computationally not effective).

Created on Thu Sep 14 17:11:27 2017

@author: ramrajvelmurugan
"""


import psycopg2
import pandas as pd
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


username = 'postgres'
password = os.environ['db_password']
db = 'tweets_db'
host = '104.154.139.71'

engine = create_engine('postgres://%s:%s@%s/%s'%(username,password,host,db))
connection = engine.connect()
neighborhoods = pd.read_sql_query("""

    select id,tags from 
    planet_osm_nodes where  
    'name' = any(tags) and 'bus_stop' != all(tags);


""",engine)
neighborhoodsWithNames = neighborhoods[
    neighborhoods.tags.astype(str).str.contains("name")]
nn = len(neighborhoodsWithNames)
# iterate for each node found in the planet_osm_nodes table 
for ind,neighborhood in neighborhoodsWithNames.iterrows():
    name = neighborhood.tags[neighborhood.tags.index("name")+1]
    id = neighborhood.id
    # find all tweets that match this node (limit to a 
    # predetermined number to not worry about nodes like 'Florida') 
    searchresults = pd.read_sql_query("""
        SELECT tweet_id FROM 
        tweets WHERE 
        document @@ phraseto_tsquery(%(name)s) limit 1000;
    """,engine,params={"name":name})
    for ind2,searchresult in searchresults.iterrows():
        insertvalues = {
            "tweet_id":int(searchresult.tweet_id),
            "osm_id":int(id)}
        sqlquery = """
            INSERT INTO osmTweetLocalization
                (tweet_id,osm_id) 
            VALUES
                (%(tweet_id)s,%(osm_id)s) 
            ON CONFLICT DO NOTHING;
        """ 
        result = connection.execute(sqlquery,params=insertvalues)
    print(str(ind)+" of "+str((nn))+": Found and recorded "+str(len(searchresults))+" tweets for "+name)