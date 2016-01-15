import os
import time
from itertools import cycle
import logging
import datetime

import config, sg_filter

import requests
from pytrends.pyGTrends import pyGTrends
import tweepy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ttp import ttp


MYUSERNAME= "atwhoispopular"

google_username= config.google["User_Name"]
google_password= config.google["Password"]

logging.basicConfig(filename='logs.log',level=logging.INFO)


def now_time():
    now = datetime.datetime.now()
    return now.strftime('[%Y/%m/%d %H:%M:%S]')


logging.info("%s Connecting to google..." % now_time())
print("%s Connecting to google..." % now_time())
MYCONNECTOR = pyGTrends(google_username, google_password)
logging.info("%s Connected to google" % now_time())
print("%s Connected to google" % now_time())
logging.info("\n")

# time to sleep if got a 420 error
BACKOFF= 2
backoff= BACKOFF

# don't respond to queries from these accounts
BLACKLIST = [
    "pixelsorter",
    "lowpolybot",
    "slashkarebear",
    "slashgif",
    "slashremindme"
]

TIME_SPAN_OPTIONS= [str(a)+ "y" for a in range(1, 12)]
TIME_SPAN_OPTIONS+= [str(a)+ "m" for a in range(1, 91)]
TIME_SPAN_OPTIONS+= [str(a)+ "d" for a in range(1, 91)]


def getGoogleTrends(searchterms, period= None):
    connector= MYCONNECTOR

    connector.request_report(keywords= searchterms, date= period)
    data= connector.get_data()

    if "An error has been detected" in data:
        return("Check the format of your date and keywords.")
    elif "Interest over time" in data:
        return data
    else:
        return("Provided keywords have less traffic to compare.")


def savePlotData(timeseries_title, timeseries_data, tweet_id, tweet_from):
    filename= None
    plt.figure()

    time_axis= [i+1 for i in range(len(timeseries_data))]
    #custom x labels
    time_ticks_diff= int(len(timeseries_data)/5)
    time_ticks= [1, time_ticks_diff, 2*time_ticks_diff, 3*time_ticks_diff, 4*time_ticks_diff, len(timeseries_data)-1]

    time_labels= [timeseries_data[a][0] for a in time_ticks]
    #change latest
    if timeseries_title[0]== "Time":
        time_labels[-1]= "Now"
    elif timeseries_title[0]== "Day":
        time_labels[-1]= "Today"
    else:
        time_labels[-1]= "This week"

    plt.xticks(time_ticks, time_labels)

    lines_styles = ["-","--","-.",":","-"]
    linestyle_cycler = cycle(lines_styles)
    lines_widths = [2, 2, 3, 3, 3]
    linewidth_cycler= cycle(lines_widths)

    for i in range(len(timeseries_title)- 1):
        y_axis= [(a[i+1]) for a in timeseries_data]
        y_axis= ["0" if a==" " else a for a in y_axis]
        y_axis= [int(a) for a in y_axis]
        y_axis_smooth= sg_filter.savitzky_golay(y_axis, 11, 3)
        y_axis_smooth= [0 if a<0 else a for a in y_axis_smooth]

        plt.plot(time_axis, y_axis_smooth, linewidth=next(linewidth_cycler), linestyle=next(linestyle_cycler), label=timeseries_title[i+1])

    plt.xlabel(timeseries_title[0])
    plot_title= [a[0].upper()+ a[1:] for a in timeseries_title[1:]]
    plt.title(" vs. ".join(plot_title))
    plt.annotate("By @SnShines", xy=(0.9, 0.95),  xycoords="figure fraction", xytext=(0.9, 0.95), textcoords="figure fraction")
    plt.legend()

    current_fig= plt.gcf()
    current_fig.set_size_inches(18.5, 10.5)

    current_fig.savefig("plots/%s_%s.png" % (tweet_id, tweet_from))

    filename= "plots/%s_%s.png" % (tweet_id, tweet_from)
    return filename


def parseGoogleData(raw_data):
    top_regions= []
    scores= []
    timeseries_data= raw_data[raw_data.index("Interest over time"): raw_data.index("\n\n\n")]
    timeseries_data= timeseries_data.split("\n")
    timeseries_data= timeseries_data[1:]
    timeseries_data= [a.split(",") for a in timeseries_data]

    timeseries_title= timeseries_data[0]
    timeseries_data= timeseries_data[1:]

    for i in range(len(timeseries_title)-1):
        sum_score= 0
        for j in range(len(timeseries_data)):
            if timeseries_data[j][i+1]== " ":
                timeseries_data[j][i+1]= "0"
            sum_score+= int(timeseries_data[j][i+1])
        ave_sum_score= int(sum_score/len(timeseries_data))
        scores.append(ave_sum_score)

    for i in range(len(timeseries_title)- 1):
        raw_data= raw_data[raw_data.index("Top regions"):]
        temp_data= raw_data[:raw_data.index("\n\n")]
        temp_data= temp_data.split("\n")
        temp_data= temp_data[2]
        top_regions.append(temp_data.split(",")[0])
        raw_data= raw_data[1:]

    return timeseries_title, timeseries_data, top_regions, scores


def parseTweet(tweet_from, tweet_text):
    query= tweet_text[tweet_text.index("@%s" % MYUSERNAME)+ len("@%s" % MYUSERNAME)+ 1:]
    time_span= None

    result= ttp.Parser().parse(tweet_text)
    tagged_users = result.users + [tweet_from]
    tagged_hashtags = result.tags
    tagged_urls = result.urls

    for user in tagged_users:
        query = query.replace("@%s" % user, "")
    for tag in tagged_hashtags:
        query = query.replace("#%s" % tag, "")
    for url in tagged_urls:
        query = query.replace("%s" % url, "")

    query= query.replace(" vs. ", ", ")
    query= query.replace(" vs ", ", ")
    query= query.replace(" or ", ", ")
    query= query.replace(" and ", ", ")
    query= query.split(" ")
    query= [a for a in query if a!= ""]
    query= " ".join(query)

    if query.split(" ")[-1] in TIME_SPAN_OPTIONS:
        time_span= query.split(" ")[-1]
        query= query.split(" ")[:-1]
        query= " ".join(query)
        # convert year timespans to month
        if "y" in time_span:
            time_span= str(int(time_span[:-1])*12) + "m"
        time_span= "today "+ time_span[:-1]+ "-"+ time_span[-1]

    return tagged_users, query, time_span


def getReplyTweet(tagged_users, title, regions, scores):
    reply= "."+ " ".join("@%s" % a for a in tagged_users if a!= MYUSERNAME)+ "\n"
    title= title[1:]
    for i in range(len(title)):
        reply+= "#"+ "".join(title[i].split(" "))+ " score="+ str(scores[i])+ "; popular in "+ regions[i]+ "\n"
    # remove last new line
    reply= reply[:-1]

    if len(reply)> 115:
        reply= reply[:112]+ "..."

    return reply


class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        tweet_id= status.id
        tweet_text= status.text
        tweet_from= status.user.screen_name

        logging.info("\n")
        logging.info("%s Tweet from: %s; Id: %s" % (now_time(), tweet_id, tweet_from))
        print("%s Tweet from: %s; Id: %s" % (now_time(), tweet_id, tweet_from))
        logging.info("Tweet: %s" % tweet_text)

        if tweet_from.lower() != MYUSERNAME and tweet_from.lower() not in BLACKLIST and not hasattr(status, "retweeted_status"):
            try:
                tagged_users, tweet_query, time_span= parseTweet(tweet_from, tweet_text.lower())
            except:
                error_reply= "@%s please check the format of your tweet. I can't understand it yet!" % tweet_from
                logging.info("Error reply: %s" % error_reply)
                error_reply_status= api.update_status(status= error_reply, in_reply_to_status_id= tweet_id)
            else:
                raw_data= getGoogleTrends(tweet_query, time_span)
                logging.info("%s Got google trends data" % now_time())

                if "Interest over time" in raw_data:
                    outfile= open("trends/%s_%s.txt" % (tweet_id, tweet_from), "w")
                    outfile.write(raw_data)
                    outfile.close()

                    timeseries_title, timeseries_data, top_regions, scores= parseGoogleData(raw_data)
                    logging.info("Time series title: %s" % timeseries_title)

                    filename= savePlotData(timeseries_title, timeseries_data, tweet_id, tweet_from)

                    if filename:
                        reply_tweet= getReplyTweet(tagged_users, timeseries_title, top_regions, scores)
                        logging.info("Reply: %s" % reply_tweet)
                        reply_tweet_status= api.update_with_media(filename= filename, status= reply_tweet, in_reply_to_status_id= tweet_id)

                elif "Check" in raw_data:
                    error_reply= "@%s please check the format of your date and keywords. I am finding it difficult to parse them." % tweet_from
                    logging.info("Error reply: %s" % error_reply)
                    error_reply_status= api.update_status(status= error_reply, in_reply_to_status_id= tweet_id)
                else:
                    error_reply= "@%s provided keywords have very less traffic to compare. Choose some interesting topics!" % tweet_from
                    logging.info("Error reply: %s" % error_reply)
                    error_reply_status= api.update_status(status= error_reply, in_reply_to_status_id= tweet_id)

    def on_error(self, status_code):
        global backoff
        logging.info("%s on_error: %d" % (now_time(), status_code))

        if status_code== 420:
            backoff= backoff* 2
            logging.info("on_error: backoff %d seconds" % backoff)
            time.sleep(backoff)
            return True


if __name__== "__main__":
    # twitter oauth
    auth = tweepy.OAuthHandler(config.twitter["API_Key"], config.twitter["API_Secret"])
    auth.set_access_token(config.twitter["Access_Token"],
                          config.twitter["Access_Token_Secret"])
    api = tweepy.API(auth)

    myStreamListener= MyStreamListener()
    myStream= tweepy.Stream(auth = api.auth, listener=myStreamListener)

    if not os.path.exists('plots/'):
        os.makedirs('plots/')
    if not os.path.exists('trends/'):
        os.makedirs('trends/')

    try:
        # starts listening to twitter stream
        myStream.userstream(_with="user", replies="all")
    except Exception as e:
        logging.info("%s Stream exception: %s" % (now_time(), e))
        raise e
