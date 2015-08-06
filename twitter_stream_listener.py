#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import sys
import time
import config
import tweepy
from tweepy.utils import import_simplejson
json = import_simplejson()


class TwitterStreamListener(tweepy.StreamListener):
    """ Respond to StreamListener events and record results to DB"""

    def __init__(self, db_filename, max_results):
        """
        :param db_filename: can't get this from config b/c argv may override it
        :param max_results: same
        """
        self.counter = 0  # total tweets collected so far
        self.db_filename = db_filename
        self.max_results = max_results
        self.connect_to_db()
        self.start_stream()


    def connect_to_db(self):
        self.conn = lite.connect(self.db_filename)
        self.cursor = self.conn.cursor()


    def start_stream(self):
        auth = tweepy.OAuthHandler(config.keys['consumer_key'], config.keys['consumer_secret'])
        auth.set_access_token(config.keys['access_token'], config.keys['access_secret'])
        stream = tweepy.Stream(auth, self)

        # begin stream of incoming data events
        stream.sample()

        # can filter by language, but you have to use a keyword (track) too
        # stream.filter(track=['a'], languages=['en'])


    def on_data(self, data):
        """ Respond to incoming data - may be error or tweet
        :param data: raw json text from twitter API
        :return bool: False will exit stream, True will continue stream
        """

        # limit number of tweets recorded
        if self.counter > self.max_results:
            print "\n" + str(self.counter) + " results reached"
            self.conn.close()
            return False  # returning false will exit streamlistener

        # handle each response differently
        if 'in_reply_to_status_id' in data:  # normal and reply tweets
            self.on_status(data)
            return
        if 'delete' in data:
            delete = json.loads(data)['delete']['status']
            self.on_delete(delete['id'], delete['user_id'])
            return
        elif 'limit' in data:
            self.on_limit(json.loads(data)['limit']['track'])
            return
        elif 'warning' in data:
            warning = json.loads(data)['warnings']
            self.on_disconnect(warning)
            return
        elif 'disconnect' in data:
            if self.on_disconnect(data['disconnect']) is False:
                return False
        else:
            sys.stderr.write("Unknown message type: " + str(data))


    def on_status(self, status):
        """ Record tweet and user to db
        :param status: raw json for standard/reply tweet
        """
        data = json.loads(status)
        screen_name = data['user']['screen_name'].encode('ascii', 'ignore')
        followers_count = data['user']['followers_count'] if not None else 0
        following = data['user']['friends_count'] if not None else 0
        statuses_count = data['user']['statuses_count']
        profile_image_url = data['user']['profile_image_url']
        favorites_count = data['user']['favourites_count']
        profile_created_at = data['user']['created_at']
        user_id = int(data['user']['id'])
        tweet_location = ''
        tweet_content = data['text'].encode('ascii', 'ignore') if not None else ''
        tweet_id = int(data['id'])
        tweet_created_at = data['created_at']
        if data['place'] is not None:
            tweet_location = data['place']['full_name'] if not None else ''
        print "Tweet #{0}\t{1}\t{2}".format(self.counter, screen_name[:10], tweet_content[:100].replace('\r', ' ').replace('\n', ' ') )

        # add the user and tweet to the database - there may be duplicates of either
        try:
            self.cursor.execute('''INSERT INTO user (
                id, screen_name, followers, following, favorites_count, statuses_count, profile_image_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (user_id, screen_name, followers_count, following, favorites_count, statuses_count, profile_image_url, profile_created_at))
        except Exception:
            print "\t# Existing User found"
        try:
            self.cursor.execute('''INSERT INTO tweet (
                    id, content, location, created_at, user)
                    VALUES (?, ?, ?, ?, ?)''',
                    (tweet_id, tweet_content, tweet_location, tweet_created_at, user_id))
        except Exception:
            print "\n# Existing Tweet found\n"

        # save change to db and log progress
        self.conn.commit()
        self.counter += 1
        return

    def on_delete(self, status_id, user_id):
        try:
            self.cursor.execute('''DELETE FROM tweet WHERE id=? AND user=?''', (status_id, user_id))
            print "DELETED: ", status_id
        except Exception as e:
            print "\n*** Delete failed\n"
            print e
        return

    def on_limit(self, track):
        # if limit is hit, there are more tweets than can be shown to use at our current rate
        # track is the number of tweets that we're not seeing
        # https://dev.twitter.com/streaming/overview/messages-types#limit_notices
        sys.stderr.write("# " + str(track) + " more tweets not shown\n")
        return

    def on_timeout(self):
        sys.stderr.write("\n*** Timeout, sleeping for 60 seconds...\n")
        time.sleep(60)
        return

    def on_warning(self, notice):
        sys.stderr.write("\n*** Warning: " + str(notice["message"]))
        return

    def on_error(self, status_code):
        sys.stderr.write('\n*** Error: ' + str(status_code) + "\n")
        return False

    def on_disconnect(self, notice):
        """Called when twitter sends a disconnect notice
        Disconnect codes are listed here:
        https://dev.twitter.com/docs/streaming-apis/messages#Disconnect_messages_disconnect
        """
        sys.stderr.write("\n*** Disconnected, reason" + str(notice))
        return False

