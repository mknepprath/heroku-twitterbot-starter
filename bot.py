import os
import time
import string
import random
import tweepy
import psycopg2
import urlparse
import json

debug = True
delete_tweets = False

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = conn.cursor()

class TwitterAPI:
    """
    Class for accessing the Twitter API.

    Requires API credentials to be available in environment
    variables. These will be set appropriately if the bot was created
    with init.sh included with the heroku-twitterbot-starter
    """
    def __init__(self):
        consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
        consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def tweet(self, message):
        """Send a tweet"""
        self.api.update_status(status=message)

    def reply(self, message, tweetid):
        """Reply to a tweet"""
        self.api.update_status(status=message, in_reply_to_status_id=tweetid)

if __name__ == "__main__":
    twitter = TwitterAPI()

    # deletes all tweets so far
    if delete_tweets == True:
        for status in tweepy.Cursor(twitter.api.user_timeline).items():
            try:
                print status.text
                twitter.api.destroy_status(status.id)
            except:
                pass

    # init mentions
    mentions = []

    if debug == False:
        # go through mentions from Twitter using Tweepy
        for mention in tweepy.Cursor(twitter.api.mentions_timeline).items():
            try:
                # splits tweet at first space, game_name = @familiarlilt (this should probably happen in the next loop)
                mention_len = len((mention.text).split())
                if mention_len == 1:
                    tweet = ''
                else:
                    game_name, tweet = (mention.text).split(' ',1)

                # init mentioned
                mentioned = False
                # runs through mentions and notes if current user has been mentioned
                for m in mentions:
                    try:
                        if mention.user.id == m['user_id']:
                            mentioned = True
                    except:
                        pass

                # if user hasn't been mentioned, append it to mentions
                if mentioned == False:
                    mentions.append({
                        'screen_name': mention.user.screen_name,
                        'user_id': mention.user.id,
                        'tweet': tweet,
                        'tweetid': mention.id
                    })

            except:
                pass

    if debug == True:
        # just for testing purposes
        mentions.append({
            'screen_name': 'mknepprath',
            'user_id': 15332057,
            'tweet': 'drop banana', # update this with tweet to test
            'tweetid': 703619369989853185
        })

    for mention in mentions:
        try:
            screen_name = mention['screen_name']
            user_id = mention['user_id']
            tweet = mention['tweet']
            tweetid = mention['tweetid']
            reply = False

            # attempts to grab current user from users table
            cur.execute("""SELECT 1 FROM users WHERE id = %s;""", (str(user_id),))
            user_exists = cur.fetchone()
            # if they're in the table, grab tweet id from table
            if user_exists != None:
                print "current player: " + screen_name
                cur.execute("""SELECT 1 FROM users WHERE last_tweet_id = %s;""", (str(tweetid),))
                tweet_exists = cur.fetchone()
                # if tweetid isn't in users table, update tweetid
                if tweet_exists == None:
                    print "new tweet"
                    cur.execute("UPDATE users SET last_tweet_id = %s WHERE id = %s;", (tweetid, str(user_id)))
                    reply = True
                    conn.commit()
                # otherwise, do nothing - tweet has already been replied to
                else:
                    print "old tweet"
            else:
                # if user is not in the users table, add user and tweetid
                print "new player: " + screen_name
                cur.execute("INSERT INTO users (name, id, last_tweet_id) VALUES (%s, %s, %s)", (screen_name, user_id, tweetid))
                reply = True
                conn.commit()

            if debug == True:
                reply = True

            # might want to add double check to make sure tweet sent
            # if this mention should be replied to, do so
            if reply == True:
                print "tweet: " + tweet

                # removes punctuation and makes move lowercase
                exclude = set(string.punctuation)
                move = ''.join(ch for ch in tweet if ch not in exclude).lower()
                print "move: " + move

                # get position
                cur.execute("SELECT position FROM users WHERE id = %s;", (str(user_id),))
                user = cur.fetchone()
                position = user[0]
                print "position: " + position

                # get inventory
                cur.execute("SELECT inventory FROM users WHERE id = %s;", (str(user_id),))
                inv = cur.fetchone()
                inventory = json.loads(inv[0])

                # randstring to avoid Twitter getting mad about duplicate tweets
                randstring = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

                # break apart tweet to figure out intent - should go in reply check
                tweet_len = len((tweet).split())

                if tweet_len == 1:
                    print 'one word tweet: ' + tweet
                else:
                    # a will be the basic command if there is one
                    a, b = (tweet).split(' ',1)

                if a == 'drop':
                    print 'so you want to drop ' + b
                    # need to add check to make sure this is 1) an actual item, 2) one you have, 3) and delete it if you only have one
                    if b not in inventory:
                        message = '@' + screen_name + ' You don\'t have any of those. ' + randstring
                        print "reply: " + message
                    elif inventory[b]['quantity'] <= 0:
                        del inventory[b]
                        cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id),))
                        conn.commit()
                        message = '@' + screen_name + ' You drop one ' + b + '.' + randstring
                        print "reply: " + message
                    else:
                        inventory[b]['quantity'] -= 1
                        cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id),))
                        conn.commit()
                elif a == 'give':
                    # c will be the item, and b should be the recipient
                    b, c = (b).split(' ',1)
                    print 'so you want to give ' + c + ' to ' + b
                # if move is start, init game - otherwise give error
                elif (move == "start") and (position == "start"):
                    cur.execute("UPDATE users SET position = 'room' WHERE id = %s;", (str(user_id),))
                    conn.commit()
                    message = '@' + screen_name + ' You wake up in an unfamiliar room. ' + randstring
                    print "reply: " + message
                    if debug == False:
                        twitter.reply(message, tweetid)
                elif (move == "look around") and (position == "room"):
                    message = '@' + screen_name + ' It\'s pretty neat in here. ' + randstring
                    print "reply: " + message
                    if debug == False:
                        twitter.reply(message, tweetid)
                elif (move == "pick up apple") and (position == "room"): # anatomy of a move
                    # update values here: items, triggers, etc
                    inventory['apple']['quantity'] += 1
                    # update database with updated values
                    cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id),))
                    conn.commit()
                    # formulate reply message and print it to the console
                    message = '@' + screen_name + ' You acquired an apple. ' + randstring
                    print "reply: " + message
                    # send to Twitter when not debugging
                    if debug == False:
                        twitter.reply(message, tweetid)
                elif (move == "pick up banana") and (position == "room"):
                    inventory['banana']['quantity'] += 1
                    cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id),))
                    conn.commit()
                    message = '@' + screen_name + ' You acquired a banana. ' + randstring
                    print "reply: " + message
                    if debug == False:
                        twitter.reply(message, tweetid)
                elif (move == "inventory"):
                    items = list(inventory.keys())
                    i = 0
                    while i < len(items):
                        iq = inventory[items[i]]['quantity'] # item quantity (items[i] would resolve to item's name)
                        if iq > 1: # only append quantity info if more than one
                            items[i] += ' ' + u'\u2022'*iq
                        i += 1
                    message = '@' + screen_name + ' ' + ', '.join(items)
                    print "reply: " + message
                    if debug == False:
                        twitter.reply(message, tweetid)
                else:
                    message = '@' + screen_name + ' Oops, didn\'t work. ' + randstring
                    print "reply: " + message
                    if debug == False:
                        twitter.reply(message, tweetid)
        except:
            pass

cur.close()
conn.close()
