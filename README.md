# Twitter Stream Recorder

Collect and store tweets and Twitter users in a SQLite database using Twitter's streaming API, Python and Tweepy.

### Requirements
* [Twitter API key and OAuth access token](https://dev.twitter.com/oauth/overview/application-owner-access-tokens)
* [Tweepy](https://pypi.python.org/pypi/tweepy)
* SQLite3
* Python

### Usage
1. `cp config.sample.py config.py`
2. Add your API keys to `config.py`.
3. `python stream_monitor.py` 

You can set the database name and maximum number of results in config.py or you can use command line arguments:
`python stream_monitor.py db_filename max_results`

### Notes
* We save room in the tweet DB for retweet and favorite counts, but because this is a real-time stream we will have to do another pass later to check for updated stats.  
* Twitter uses Unicode so watch out for encoding errors with SQLite.
* [Twitter Streaming API reference](https://dev.twitter.com/streaming/reference/get/statuses/sample)
