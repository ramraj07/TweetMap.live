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
import time


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
testi = ''
globalcounter =0
def callback(message):
    #print('Received message: {}'.format(message))
    global testi
    try:
        line = message.data.replace('\\u0000'.encode(),''.encode())
        testi = line
        #print(line[1:250])
        temp = json.loads(line)
        if not 'user' in temp.keys():
            return
        userdict = temp['user']
    #    try:
        if session.query(Tweets.tweet_id).filter_by(tweet_id=temp['id']).scalar() is not None:
            return
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
            lng = temp['geo']['coordinates'][0]
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
        global globalcounter
        globalcounter = globalcounter+1
        if globalcounter%10000 ==0:
            print('Added '+str(globalcounter)+' tweets!')
        #print('Added tweet '+temp['text'][1:50])
    except:
        print('Error loading tweet.')
    

client.subscribe(subscription_path,callback=callback)


while True:
        time.sleep(60)



#
#
#print('Opening file...')
#fpin= gzip.open('../tweets6.json.gz')
#i=0
#line = fpin.readline()
#dd =[json.loads(line)]
##%%
#ngeos=0
#tempi = 0
#nerrors=0
#print('Starting to read...')
#for line in fpin.readlines():
#    if len(line)<3:
#        continue
#    
#    i=i+1
#    tempi = tempi+1
#    if tempi>3000:
#        print('Read '+str(i)+' tweets')
#        tempi=0
#    line = line.replace('\\u0000'.encode(),''.encode())
#    temp = json.loads(line)
#    #%
#    if not 'user' in temp.keys():
#        continue
#    userdict = temp['user']
##    try:
#    if session.query(Tweets.tweet_id).filter_by(tweet_id=temp['id']).scalar() is not None:
#        continue
#    if session.query(Users.id).filter_by(id=userdict['id']).scalar() is None:
#        if userdict['url'] is None:
#            userdict['url'] = '-'
#        if userdict['location'] is None:
#            userdict['location']=''
#        new_user = Users(id=userdict['id'],
#                        name=userdict['name'],
#                        screen_name = userdict['screen_name'],
#                        location=userdict['location'],
#                        url=userdict['url'],
#                        description=userdict['description'],
#                        verified=userdict['verified'],
#                        followers_count = userdict['followers_count'],
#                        friends_count = userdict['friends_count'],
#                        statuses_count=  userdict['statuses_count'],
#                        geo_enabled = userdict['geo_enabled'],
#                        lang = userdict['lang'],
#                        created_at=parser.parse(userdict['created_at']),
#                        profile_background_image_url = userdict['profile_image_url'])
#        session.add(new_user)
#        session.commit()
#        session.flush()
#    placedict = temp['place']
#    if placedict is not None:
#        if session.query(Place.id).filter_by(id=placedict['id']).scalar() is None:
#            new_place = Place(id=placedict['id'],
#                              url=placedict['url'],
#                              place_type=placedict['place_type'],
#                              name=placedict['name'],
#                              full_name=placedict['full_name'],
#                              bounding_box_json = json.dumps(placedict['bounding_box']))
#            session.add(new_place)
#            session.commit()
#            session.flush()
#        placeid = temp['place']['id']
#    else:
#        placeid = ''
#    if temp['geo'] is not None:
#        lat = temp['geo']['coordinates'][0]
#        lng = temp['geo']['coordinates'][0]
#    else:
#        lat=0
#        lng=0
#    
#    if placeid=='':
#        new_tweet = Tweets(
#                tweet_id=temp['id'],
#                tweet_text=temp['text'],
#                tweet_source=temp['source'],
#                in_reply_to_status_id=temp['in_reply_to_status_id'],
#                in_reply_to_user_id=temp['in_reply_to_user_id'],
#                tweet_date=parser.parse(temp['created_at']),
#                geo_lat=lat,
#                user_id= temp['user']['id'],
#                geo_lng=lng)
#            
#    else:        
#        new_tweet = Tweets(
#                tweet_id=temp['id'],
#                tweet_text=temp['text'],
#                tweet_source=temp['source'],
#                in_reply_to_status_id=temp['in_reply_to_status_id'],
#                in_reply_to_user_id=temp['in_reply_to_user_id'],
#                tweet_date=parser.parse(temp['created_at']),
#                place_id=placeid,
#                geo_lat=lat,
#                user_id= temp['user']['id'],
#                geo_lng=lng)
#            
#    session.add(new_tweet)
#    session.commit()
#    except:
#         nerrors = nerrors+1
#         if nerrors<1000:
#             print('Error entering tweet with id '+str(temp['id']))
#         else:
#             print('Errors happened a thousand times, so stopping.')
#             break
#                 
                        
#class Users(Base):
#    __tablename__ = 'users'
#    id = Column(Integer,primary_key = True)
#    name = Column(String(1000))
#    screen_name = Column(String(1000))
#    location = Column(String(1000))
#    url = Column(String(2000))
#    description = Column(String(3000))
#    verified = Column(types.Boolean)
#    followers_count = Column(Integer)
#    friends_count = Column(Integer)
#    statuses_count = Column(Integer)
#    geo_enabled = Column(types.Boolean)
#    lang = Column(String)
#    created_at = Column(types.DateTime)
#    profile_background_image_url = Column(String(2000))
#
#class Place(Base):
#    __tablename__ = 'place'
#    id = Column(String(50),primary_key=True)
#    url = Column(String(2000))
#    place_type = Column(String(100))
#    name = Column(String(500))
#    full_name = Column(String(2000))
#    bounding_box_json = Column(String(5000))
#    
#class Tweets(Base):
#    __tablename__ = 'tweets'
#    tweet_id = Column(Integer,primary_key=True)
#    tweet_text = Column(String(1000))
#    tweet_source=Column(String(1000))
#    in_reply_to_status_id = Column(Integer)
#    in_reply_to_user_id = Column(Integer, ForeignKey('users.id'))
#    tweet_date = Column(types.DateTime)
#    place_id = Column(String(50),ForeignKey('place.id'))
#    geo_lat = Column(types.Float)
#    geo_lng = Column(types.Float)
    
   