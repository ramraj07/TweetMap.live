#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script reads tweets from a Google Cloud Pub/Sub queue,
and inserts them into a database after 
performing some cleanup operations on the data.

Created on Fri Sep  8 06:13:28 2017

@author: ramrajvelmurugan
"""

import json
import gzip
import psycopg2
import os
import sys
import time
from dateutil import parser
from random import randint

from google.cloud import pubsub_v1



dbname='tweets_db'
user='postgres'
host='104.154.139.71'
password = os.environ['db_password']
# Connect to the Tweets DB on Google Cloud SQL
try:
    conn = psycopg2.connect(dbname=dbname,user=user,host=host,password=password)
except:
    print ("I am unable to connect to the database")
    return
curr= conn.cursor()

# Obtain Google Cloud SDK objects that let you connect to 
# the Pub/Sub channel with the JSON tweet messages
client = pubsub_v1.SubscriberClient()
subscription_path = client.subscription_path('molten-unison-179501','read-tweets')


globalcounter =0
def callback(message):
    """
    The callback function passed to the SubscribeClient() object 
    in the Google pubsub_v1 library. This function will be called 
    once for every message that is queued in the Pub/Sub queue. 

    It takes the message parameter, extracts the message text and 
    checks if it contains a valid tweet message. If it does, then 
    the tweet is parsed into a Json object and then a series of 
    SQL insert statements are constructed depending on whether the 
    tweet itself has some place information or not. The SQL statements
    are then executed and on successful execution, the ack() method 
    is called from the message object to acknowledge that this particular
    tweet message has been handled. This ack() is also called if it 
    was found that this message did not contain a tweet (checked by 
    finding) whether there was a 'user' key in the json object). 

    The function also uses a global counter variable to print 
     

    :param message: this is the message object passed by the 
                    SubscribeClient() object. It is assumed to 
                    contain the contents of the message and an
                    ack() function that acknowledges that the 
                    particular message has been processed. 
    :returns: this is a description of what is returned
    """
    try:
        # some unicode cleanup
        line = message.data.replace('\\u0000'.encode(),''.encode())
        temp = json.loads(line)
        if not 'user' in temp.keys():
            # means this message doesn't contain a bonafide tweet
            message.ack()
            return
        userdict = temp['user']
        if userdict['url'] is None:
            # so no null URL values get loaded
            userdict['url'] = '-'
        if userdict['location'] is None:
            userdict['location']=''
        if temp['geo'] is not None:
            lat = temp['geo']['coordinates'][0]
            lng = temp['geo']['coordinates'][1]
        else:
            lat=0
            lng=0

        placedict = temp['place']
        # some tweets have place information, others don't, we need a different
        # set of SQL statements for each case.
        if placedict is not None:
            placeid = temp['place']['id']
            insertsqlplace = """
                INSERT INTO users 
                    (id, name, screen_name, location,
                    url, description, verified, followers_count, friends_count,
                    statuses_count, geo_enabled, lang, created_at,
                    profile_background_image_url) 
                VALUES
                    (%(id)s, %(name)s, %(screen_name)s, %(location)s, %(url)s,
                    %(description)s, %(verified)s, %(followers_count)s, %(friends_count)s,
                    %(statuses_count)s, %(geo_enabled)s, %(lang)s, %(created_at)s,
                    %(profile_background_image_url)s) 
                ON CONFLICT DO NOTHING;
                
                INSERT INTO place
                    (id, url, place_type, name, full_name, bounding_box_json)
                VALUES
                    (%(idp)s, %(urlp)s, %(place_typep)s, %(namep)s,
                    %(full_namep)s, %(bounding_box_jsonp)s) 
                ON CONFLICT DO NOTHING;
                
                INSERT INTO tweets 
                    (tweet_id,
                    tweet_text, tweet_source, in_reply_to_status_id, in_reply_to_user_id,
                    tweet_date, place_id, user_id, geo_lat, geo_lng) 
                VALUES 
                    (%(tweet_idt)s,
                    %(tweet_textt)s, %(tweet_sourcet)s, %(in_reply_to_status_idt)s,
                    %(in_reply_to_user_idt)s, %(tweet_datet)s, %(place_idt)s, %(user_idt)s,
                    %(geo_latt)s, %(geo_lngt)s) 
                ON CONFLICT DO NOTHING;
                """
            parametersplace = {'id': userdict['id'],
                'name': userdict['name'],
                'screen_name': userdict['screen_name'],
                'location': userdict['location'],
                'url': userdict['url'],
                'description': userdict['description'],
                'verified': userdict['verified'],
                'followers_count': userdict['followers_count'],
                'friends_count': userdict['friends_count'],
                'statuses_count': userdict['statuses_count'],
                'geo_enabled': userdict['geo_enabled'],
                'lang': userdict['lang'],
                'created_at': parser.parse(userdict['created_at']),
                'profile_background_image_url': userdict['profile_image_url'],
                'idp': placedict['id'],
                'urlp': placedict['url'],
                'place_typep': placedict['place_type'],
                'namep': placedict['name'],
                'full_namep': placedict['full_name'],
                'bounding_box_jsonp': json.dumps(placedict['bounding_box']),
                'tweet_idt': temp['id'],
                'tweet_textt': temp['text'],
                'tweet_sourcet': temp['source'],
                'in_reply_to_status_idt': temp['in_reply_to_status_id'],
                'in_reply_to_user_idt': temp['in_reply_to_user_id'],
                'tweet_datet': parser.parse(temp['created_at']),
                'place_idt': placeid,
                'user_idt': temp['user']['id'],
                'geo_latt': lat, 'geo_lngt': lng}
        else:
            placeid = None
            insertsqlplace = """
                INSERT INTO users 
                    (id, name, screen_name, location,
                    url, description, verified, followers_count, friends_count,
                    statuses_count, geo_enabled, lang, created_at,
                    profile_background_image_url) 
                VALUES
                    (%(id)s, %(name)s, %(screen_name)s, %(location)s, %(url)s,
                    %(description)s, %(verified)s, %(followers_count)s, %(friends_count)s,
                    %(statuses_count)s, %(geo_enabled)s, %(lang)s, %(created_at)s,
                    %(profile_background_image_url)s) 
                ON CONFLICT DO NOTHING;

                INSERT INTO tweets 
                    (tweet_id,
                    tweet_text, tweet_source, in_reply_to_status_id, in_reply_to_user_id,
                    tweet_date, place_id, user_id, geo_lat, geo_lng) 
                VALUES 
                    (%(tweet_idt)s,
                    %(tweet_textt)s, %(tweet_sourcet)s, %(in_reply_to_status_idt)s,
                    %(in_reply_to_user_idt)s, %(tweet_datet)s, %(place_idt)s, %(user_idt)s,
                    %(geo_latt)s, %(geo_lngt)s) 
                ON CONFLICT DO NOTHING;
                """
            parametersplace = {'id': userdict['id'],
                'name': userdict['name'],
                'screen_name': userdict['screen_name'],
                'location': userdict['location'],
                'url': userdict['url'],
                'description': userdict['description'],
                'verified': userdict['verified'],
                'followers_count': userdict['followers_count'],
                'friends_count': userdict['friends_count'],
                'statuses_count': userdict['statuses_count'],
                'geo_enabled': userdict['geo_enabled'],
                'lang': userdict['lang'],
                'created_at': parser.parse(userdict['created_at']),
                'profile_background_image_url': userdict['profile_image_url'],
                'tweet_idt': temp['id'],
                'tweet_textt': temp['text'],
                'tweet_sourcet': temp['source'],
                'in_reply_to_status_idt': temp['in_reply_to_status_id'],
                'in_reply_to_user_idt': temp['in_reply_to_user_id'],
                'tweet_datet': parser.parse(temp['created_at']),
                'place_idt': placeid,
                'user_idt': temp['user']['id'],
                'geo_latt': lat, 'geo_lngt': lng}
        curr.execute(insertsqlplace,parametersplace)
        # commit the insert statements to the data base and then acknowledge
        # parsing of the message if successful.
        conn.commit()
        message.ack()
        if round(randint(0, 50000)/100)==250:
            print('Added ~'+str(250)+' tweets! '+temp['created_at'])
    except:
        print('Error loading tweet.')

# This line is where we subscribe the Pub/Sub channel and assign our "callback"
# function as the receiver
client.subscribe(subscription_path,callback=callback)

# keep this program open while the callbacks continuously execute.
while True:
        time.sleep(60)
