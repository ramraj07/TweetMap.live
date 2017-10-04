from flask import render_template, redirect,url_for
from tweetmapflask import app
from flask import request
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
from flask import jsonify
import string


user = 'postgres' #add your username here (same as previous postgreSQL)                      
host = '104.154.139.71'
dbname = 'tweets_db'
password=os.environ['db_password']
con = None
con = psycopg2.connect(host=host,database = dbname, user = user,password=password)
cur = con.cursor()


# set up translator to remove non-digit characters
allchars = ''.join(chr(i) for i in xrange(256))
identity = string.maketrans('', '')
nondigits = allchars.translate(identity, string.digits)


@app.route('/')
@app.route('/index')
def index():
    return app.send_static_file('index.html')

    
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/abouttweetmap')
def abouttweetmap():
    return render_template('about-tweetmap.html')


@app.route('/train',methods=['GET','POST'])
def train():
    
    defn = 3
    MAXRESULTS = 100
    try:
       nresults = request.args['n']
       toint = int(nresults)
       if toint>0 and toint < MAXRESULTS:
           defn = toint
    except:
        defn=3
    
    sql_query = """
        select 
            tweets.tweet_text,tweets.tweet_id 
        from tweets 
        join tweetsTrainLocation01 
        on tweets.tweet_id = tweetsTrainLocation01.tweet_id 
        where isALocationTweet is null 
        order by random() 
        limit @(nresults)s;
    """

    query_results=pd.read_sql_query(sql_query,params={"nresults":defn},con)
    tweets = []
    for i in range(0,query_results.shape[0]):
        tweets.append(dict(index=query_results.iloc[i]['tweet_id'], tweet=query_results.iloc[i]['tweet_text']))
    ntweets = query_results.shape[0];
    return render_template('tweetstrain.html',ntweets=ntweets,tweets=tweets)


@app.route('/submit',methods=['POST'])
def submit():
    ntweetscoming = request.form['ntweets']
    if ntweetscoming is not None:
        print('theres post')
        print (request.form)
        trueids = []
        falseids = []
        for i in range (0,int(ntweetscoming)):
            tweetid = request.form['tweetid-'+str(i)].translate(identity,nondigits)
            if 'check-'+str(i) in request.form:
                trueids.append(tweetid)
                print(tweetid+' is checked')
            else:
                falseids.append(tweetid)
        sqlt = ""
        sqlf = ""
        if len(trueids)!=0:  
            trueidsString = ",".join(trueids)
            # Note - the ids have already been cleaned up of non-integer values.
            sqlt = "update tweetsTrainLocation01 set isalocationtweet = True,ipaddress=@(ipaddr)s,created_at=now() where tweet_id in ("%request.remote_addr
            sqlt = sqlt+trueidsString+");"
        if len(falseids)!=0:
            falseidsString = ",".join(falseids)
            # Note - the ids have already been cleaned up of non-integer values.
            sqlf = "update tweetsTrainLocation01 set isalocationtweet = False,ipaddress=@(ipaddr)s,created_at=now() where tweet_id in ("%request.remote_addr
            sqlf = sqlf+falseidsString+");"
        cur.execute(sqlt+sqlf)
        con.commit()
        print(sqlt)
        print(sqlf)
    else:
        print('no post')
    return redirect(url_for("train",n=ntweetscoming))