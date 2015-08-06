#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import sys
import time
import config
from twitter_stream_listener import TwitterStreamListener


class StreamMonitor():
    """ Create and monitor a listener for the twitter streaming API"""

    def __init__(self, db_filename, max_results):
        """ Setup DB connection and tables
        :param db_filename: relative path and filename for SQLite database
        :param max_results: total number of tweets to record
        """
        self.db_filename = db_filename
        self.max_results = max_results
        self.counter = 0  # total tweets collected so far

        try:
            self.conn = lite.connect(db_filename)
            self.cursor = self.conn.cursor()
            self.create_database()
            self.conn.close() # no longer need db from this object
        except Exception as e:
            print "Could not connect to SQLite database"
            print e
            quit()


    def create_database(self):
        """ Create empty user and tweet tables """
        self.cursor.execute('drop table if exists user')
        self.cursor.execute('''create table user(
            id INTEGER PRIMARY KEY,
            screen_name TEXT,
            followers INTEGER,
            following INTEGER,
            favorites_count INTEGER,
            statuses_count INTEGER,
            profile_image_url TEXT,
            created_at TEXT)''')
        self.cursor.execute('drop table if exists tweet')
        self.cursor.execute('''create table tweet(
            id INTEGER PRIMARY KEY,
            content TEXT,
            retweet_count INTEGER,
            favorite_count INTEGER,
            location TEXT,
            created_at TEXT,
            user INTEGER REFERENCES users(id) ON UPDATE CASCADE)''')
        self.conn.commit()


    def start_stream(self):
        """ Create the stream listener and recover from disconnections """
        start_time = time.time()
        listener = TwitterStreamListener(self.db_filename, self.max_results)
        try:
            listener.start_stream()
        except Exception as e:
            print e

        print "Time elapsed: " + str(time.time() - start_time) + " sec."



def main(argv):
    """
    Change db_filename and max_results in config.py or override with command line args.
    Usage: twitter_stream_listener.py db_filename max_results
    Or simply: twitter_stream_listener.py
    :param argv: command line args
    """

    db_filename = argv[1] if len(sys.argv) > 1 else config.preferences['db_filename']
    max_results = int(argv[2]) if len(sys.argv) > 2 else config.preferences['max_results']

    monitor = StreamMonitor(db_filename, max_results)
    monitor.start_stream()  # this continues until it returns false


if __name__ == "__main__":
    main(sys.argv)
