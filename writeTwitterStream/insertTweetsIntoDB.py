#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script reads tweet json dumps from streaming.py, extracts the geo-coded 
tweets, and otputs javascript that can be added to mapdemo.html for making a 
demonstration of tweet locations.

Created on Fri Sep  8 06:13:28 2017

@author: ramrajvelmurugan
"""

import json
import gzip
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dateutil import parser
from createDBandTables import Users,Place,Tweets

#%%
# initial tests were done on a local database
dbname = 'tweets4'
username = 'ramrajvelmurugan'

engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
print (engine.url)
#%%
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# This python file assumes that tweets that came out of readTweets.py were
# gzipped and put in the folder above this directory, for processing.
print('Opening file...')
fpin= gzip.open('../tweets2.json.gz')
i=0
line = fpin.readline()
dd =[json.loads(line)]
#%%
ngeos=0
tempi = 0
nerrors=0
print('Starting to read...')
for line in fpin.readlines():
    if len(line)<3:
        continue    
    i=i+1
    tempi = tempi+1
    if tempi>3000:
        print('Read '+str(i)+' tweets')
        tempi=0
    temp = json.loads(line)
    #%
    if not 'user' in temp.keys():
        continue
    userdict = temp['user']
    if session.query(Tweets.tweet_id).filter_by(tweet_id=temp['id']).scalar() is not None:
        continue
    if session.query(Users.id).filter_by(id=userdict['id']).scalar() is None:
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
