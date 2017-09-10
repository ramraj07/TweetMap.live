#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script reads tweets from a Google Cloud Pub/Sub queue,
and inserts them into a database through SQLAlchemy after 
performing some cleanup operations on the data.

Created on Fri Sep  8 06:13:28 2017

@author: ramrajvelmurugan
"""

import json
import gzip
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dateutil import parser
from createDBandTablesGCE import Users,Place,Tweets

from sqlalchemy import types 
from sqlalchemy_utils import database_exists, create_database
import psycopg2

import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from google.cloud import pubsub_v1

#%%
host = '104.154.139.71'
db = 'tweets_db'
uname = 'postgresql'
password = os.environ['db_password']

engine = create_engine('postgresql://'+uname+':'+password+'@'+host+'/'+db)

if not database_exists(engine.url):
    print('Database NOT FOUND!!')

#%%
Base = declarative_base()

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
client = pubsub_v1.SubscriberClient()
subscription_path = client.subscription_path('molten-unison-179501','read-tweets')
def callback(message):
    #print('Received message: {}'.format(message))
    line = line.replace('\\u0000'.encode(),''.encode())
    temp = json.loads(line)
    if not 'user' in temp.keys():
        continue
    userdict = temp['user']
    if session.query(Tweets.tweet_id).filter_by(tweet_id=temp['id']).scalar() is not None:
        continue
    if session.query(Users.id).filter_by(id=userdict['id']).scalar() is None:
        if userdict['url'] is None:
            userdict['url'] = '-'
        if userdict['location'] is None:
            userdict['location']=''
        new_user = Users(id=userdict['id'],
                        name=userdict['name'],
                        screen_name = userdict['screen_name'],
                        location=userdict['location'],
                        url=userdict['url'],
                        description=userdict['description'],
                        verified=userdict['verified'],
                        followers_count = userdict['followers_count'],
                        friends_count = userdict['friends_count'],
                        statuses_count=  userdict['statuses_count'],
                        geo_enabled = userdict['geo_enabled'],
                        lang = userdict['lang'],
                        created_at=parser.parse(userdict['created_at']),
                        profile_background_image_url = userdict['profile_image_url'])
        session.add(new_user)
        session.commit()
        session.flush()
    placedict = temp['place']
    if placedict is not None:
        if session.query(Place.id).filter_by(id=placedict['id']).scalar() is None:
            new_place = Place(id=placedict['id'],
                              url=placedict['url'],
                              place_type=placedict['place_type'],
                              name=placedict['name'],
                              full_name=placedict['full_name'],
                              bounding_box_json = json.dumps(placedict['bounding_box']))
            session.add(new_place)
            session.commit()
            session.flush()
        placeid = temp['place']['id']
    else:
        placeid = ''
    if temp['geo'] is not None:
        lat = temp['geo']['coordinates'][0]
        lng = temp['geo']['coordinates'][1]
    else:
        lat=0
        lng=0
    if placeid=='':
        new_tweet = Tweets(
                tweet_id=temp['id'],
                tweet_text=temp['text'],
                tweet_source=temp['source'],
                in_reply_to_status_id=temp['in_reply_to_status_id'],
                in_reply_to_user_id=temp['in_reply_to_user_id'],
                tweet_date=parser.parse(temp['created_at']),
                geo_lat=lat,
                user_id= temp['user']['id'],
                geo_lng=lng)
            
    else:        
        new_tweet = Tweets(
                tweet_id=temp['id'],
                tweet_text=temp['text'],
                tweet_source=temp['source'],
                in_reply_to_status_id=temp['in_reply_to_status_id'],
                in_reply_to_user_id=temp['in_reply_to_user_id'],
                tweet_date=parser.parse(temp['created_at']),
                place_id=placeid,
                geo_lat=lat,
                user_id= temp['user']['id'],
                geo_lng=lng)
    session.add(new_tweet)
    session.commit()
    message.ack()
    print('Added tweet '+temp['text'][1:50])
client.subscribe(subscription_path,callback=callback)