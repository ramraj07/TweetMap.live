#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  8 14:51:46 2017
Connects to Cloud SQL postgres server and creates the initial table structure. 
To be run from the cloud compute engine vms.
@author: ramrajvelmurugan
"""

from sqlalchemy import create_engine
from sqlalchemy import types 
from sqlalchemy_utils import database_exists, create_database
import psycopg2


import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
#%%
password = os.environ['db_password']
 engine = create_engine('postgresql://postgres:%s@104.154.139.71/tweets_db'%password)
print (engine.url)

## create a database (if it doesn't exist)
if not database_exists(engine.url):
    print('Database NOT FOUND!!')
#%%

#%%
Base = declarative_base()
#%%
class Users(Base):
    __tablename__ = 'users'
    id = Column(types.BigInteger,primary_key = True)
    name = Column(String(1000))
    screen_name = Column(String(1000))
    location = Column(String(1000))
    url = Column(String(2000))
    description = Column(String(3000))
    verified = Column(types.Boolean)
    followers_count = Column(types.BigInteger)
    friends_count = Column(types.BigInteger)
    statuses_count = Column(types.BigInteger)
    geo_enabled = Column(types.Boolean)
    lang = Column(String)
    created_at = Column(types.DateTime)
    profile_background_image_url = Column(String(2000))

class Place(Base):
    __tablename__ = 'place'
    id = Column(String(50),primary_key=True)
    url = Column(String(2000))
    place_type = Column(String(100))
    name = Column(String(500))
    full_name = Column(String(2000))
    bounding_box_json = Column(String(5000))
    
class Tweets(Base):
    __tablename__ = 'tweets'
    tweet_id = Column(types.BigInteger,primary_key=True)
    tweet_text = Column(String(1000))
    tweet_source=Column(String(1000))
    in_reply_to_status_id = Column(types.BigInteger)
    in_reply_to_user_id = Column(types.BigInteger)
    tweet_date = Column(types.DateTime)
    place_id = Column(String(50),ForeignKey('place.id'))
    user_id = Column(types.BigInteger,ForeignKey('users.id'))
    geo_lat = Column(types.Float)
    geo_lng = Column(types.Float)
    
Base.metadata.create_all(engine)
#Base = declarative_base()
# 
#class Person(Base):
#    __tablename__ = 'person'
#    # Here we define columns for the table person
#    # Notice that each column is also a normal Python instance attribute.
#    id = Column(Integer, primary_key=True)
#    name = Column(String(250), nullable=False)
# 
#class Address(Base):
#    __tablename__ = 'address'
#    # Here we define columns for the table address.
#    # Notice that each column is also a normal Python instance attribute.
#    id = Column(Integer, primary_key=True)
#    street_name = Column(String(250))
#    street_number = Column(String(250))
#    post_code = Column(String(250), nullable=False)
#    person_id = Column(Integer, ForeignKey('person.id'))
#    person = relationship(Person)
# 
## Create an engine that stores data in the local directory's
## sqlalchemy_example.db file.
#engine = create_engine('sqlite:///sqlalchemy_example.db')
# 
## Create all tables in the engine. This is equivalent to "Create Table"
## statements in raw SQL.
#Base.metadata.create_all(engine)
