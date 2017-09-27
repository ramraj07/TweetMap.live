from flask import render_template
from flaskexample import app
from flask import request
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2



@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")
