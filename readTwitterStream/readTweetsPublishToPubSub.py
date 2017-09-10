from __future__ import absolute_import, print_function

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from google.cloud import pubsub_v1

# this is the Google PubSub API pubilsher object to which we send the tweets.
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('molten-unison-179501','hurricane-tweets')


# Go to http://apps.twitter.com and create an app.
# The consumer key and secret will be generated for you after
access_token = os.environ['twitter_access_token']
access_token_secret = os.environ['twitter_access_secret']
consumer_key = os.environ['twitter_consumer_key']
consumer_secret = os.environ['twitter_consumer_secret']


class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.

    """
    global publisher
    global topic_path
    def on_data(self, data):
        #print(data)
        publisher.publish(topic_path,data=data.encode('utf-8'))
        return True

    def on_error(self, status):
        print(status)

if __name__ == '__main__':
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    stream = Stream(auth, l)
    stream.filter(track=['irma', 'hurricane','florida','flooding','flood','irmasos'])
