# TweetMap.live
A webapp that reads, geolocates and visualizes tweets from disaster regions, currently in Florida for Hurricane Irma.

This webapp contains 4 primary components:

1. [A tweet reading module](readTwitterStream), which reads Twitter's streaming API and publishes the Json responses (one for each tweet) into a Google Pub/Sub stream.
2. [A tweet recording module](writeTwitterStream), which reads these Json files from the Google Pub/Sub stream, parses them and records them in a Cloud SQL Postgres database.
3. [A set of processing scripts](processTweetsForLocation), which sequentially work on the recorded tweets (periodically) to extract and filter location information from these tweets and records them into a geojson file.
4. [A Flask webapp](TweetMapFlask), which visualises the geojson file on a map using Mapbox API. The webapp also has a page where users can train the tweets for the machine learning model to show better results in the future.

## Prerequisites
1. A Google Cloud account, with a Cloud SQL Postgres database and a Pub/Sub service ready to use. The current implementation can run on any webserver as long as the SQL database is authenticated to be accessed from these servers. 
2. Enable [PostGIS](http://postgis.net/) in the Postgres server (its preinstalled in Google Cloud SQL).
3. Use [OSM2pgsql](http://wiki.openstreetmap.org/wiki/Osm2pgsql) to load Openstreetmaps dataset that you will be querying in the project. The data for Florida was loaded from [geofabrik.de](https://download.geofabrik.de/north-america/us/florida.html).
4. Authentication can be performed by installation of the Google Cloud SDK in these servers, which enables the direct access of services in a Google Cloud account without usernames and passwords from within that server.  

## Deployment steps

1. Start running the file [readTweetsPublishToPubSub.py](readTwitterStream/readTweetsPublishToPubSub.py) with the correct Pub/Sub names and  Twitter API credentials, to begin publishing filtered tweets to the Pub/Sub queue.
2. The file [createCloudDBandTables.py](writeTwitterStream/createCloudDBandTables.py) can be run once to create the database and table schema required for processing these tweets.
3. Start the file [insertTweetsIntoDB.py](writeTwitterStream/insertTweetsIntoDB.py) to start reading the Pub/Sub messages, parse them and insert them into the database. This script can be run on multiple servers to increase the throughput. 
4. Run the following periodic scripts (with periodicity as per your preference):
     * Run [searchAndInsertLocationDataFromTweets.py](processTweetsForLocation/searchAndInsertLocationDataFromTweets.py) every few hours to perform a search for all the nodes in the tweets.
     * Run [doSpacyEntityRecogOnTweets.py](processTweetsForLocation/doSpacyEntityRecogOnTweets.py) every few hours (if prefered, on a separate server).
     * Run the Jupyter Notebook [2017-09-24 Make a model to categorize tweets with a location about hurricane-related events](./processTweetsForLocation/) after the above two scripts have run to retrain the model with any new data that has been generated from the website and re-predict the tweet flags for all location tweets (and generate the geojson file for the website).
5. Run the flask website using a nginx/gunicorn framework using standard methods. 
