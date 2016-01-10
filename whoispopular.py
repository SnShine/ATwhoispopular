import requests
import config, sg_filter
from pytrends.pyGTrends import pyGTrends
import tweepy
import matplotlib.pyplot as plt
import numpy as np
from itertools import cycle
import os, sys, time
from ttp import ttp


MYUSERNAME= "atwhoispopular"

google_username= config.google["User_Name"]
google_password= config.google["Password"]

print("Connecting to google")
MYCONNECTOR = pyGTrends(google_username, google_password)

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
    # plt.plot(radius, square, marker='o', linestyle='--', color='r', label='Square')

    time_axis= [i+1 for i in range(len(timeseries_data))]
    #custom x labels
    time_ticks_diff= int(len(timeseries_data)/5)
    time_ticks= [1, time_ticks_diff, 2*time_ticks_diff, 3*time_ticks_diff, 4*time_ticks_diff, len(timeseries_data)-1]
    # print(time_ticks)
    time_labels= [timeseries_data[a][0] for a in time_ticks]
    #change latest
    if timeseries_title[0]== "Time":
        time_labels[-1]= "Now"
    elif timeseries_title[0]== "Day":
        time_labels[-1]= "Today"
    else:
        time_labels[-1]= "This week"

    # print(time_labels)

    plt.xticks(time_ticks, time_labels)

    lines_styles = ["-","--","-.",":","--"]
    linestyle_cycler = cycle(lines_styles)
    lines_widths = [2, 2, 3, 3, 2]
    linewidth_cycler= cycle(lines_widths)

    for i in range(len(timeseries_title)- 1):
        y_axis= [(a[i+1]) for a in timeseries_data]
        y_axis= ["0" if a==" " else a for a in y_axis]
        y_axis= [int(a) for a in y_axis]
        y_axis_smooth= sg_filter.savitzky_golay(y_axis, 11, 3)

        #plt.plot(time_axis, y_axis, linewidth=2, c="purple")
        plt.plot(time_axis, y_axis_smooth, linewidth=next(linewidth_cycler), linestyle=next(linestyle_cycler), label=timeseries_title[i+1])

    plt.xlabel(timeseries_title[0])
    plt.title('By @SnShines')
    plt.legend()

    current_fig= plt.gcf()
    current_fig.set_size_inches(18.5, 10.5)

    current_fig.savefig("%s_%s.png" % (tweet_id, tweet_from))


def parseGoogleData(raw_data):
    timeseries_data= raw_data[raw_data.find("Interest over time"): raw_data.find("\n\n\n")]
    timeseries_data= timeseries_data.split("\n")
    timeseries_data= timeseries_data[1:]
    timeseries_data= [a.split(",") for a in timeseries_data]

    timeseries_title= timeseries_data[0]
    timeseries_data= timeseries_data[1:]

    return timeseries_title, timeseries_data


def parseTweet(tweet_from, tweet_text):
    query= tweet_text[tweet_text.index("@%s" % MYUSERNAME)+ len("@%s" % MYUSERNAME)+ 1:]
    time_span= None

    result= ttp.Parser().parse(tweet_text)
    tagged_users = result.users + [tweet_from]
    tagged_hashtags = result.tags
    tagged_urls = result.urls

    for user in tagged_users:
        query = query.replace('@%s' % user, '')
    for tag in tagged_hashtags:
        query = query.replace('#%s' % tag, '')
    for url in tagged_urls:
        query = query.replace('%s' % url, '')

    query= query.replace(" vs. ", ", ")
    query= query.replace(" vs ", ", ")
    query= query.split(" ")
    query= [a for a in query if a!= ""]
    query= " ".join(query)

    time_span_options= [str(a)+ "y" for a in range(1, 12)]
    time_span_options+= [str(a)+ "m" for a in range(1, 91)]
    time_span_options+= [str(a)+ "d" for a in range(1, 91)]
    #print(time_span_options)

    if query.split(" ")[-1] in time_span_options:
        time_span= query.split(" ")[-1]
        query= query.split(" ")[:-1]
        query= " ".join(query)
        # convert year timespans to month
        if "y" in time_span:
            time_span= str(int(time_span[:-1])*12) + "m"
        time_span= "today "+ time_span[:-1]+ "-"+ time_span[-1]

    return tagged_users, query, time_span


class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        tweet_id= status.id
        tweet_text= status.text
        tweet_from= status.user.screen_name

        print(tweet_id)
        print(tweet_from)
        print(tweet_text)

        if tweet_from.lower() != MYUSERNAME and not hasattr(status, "retweeted_status"):
            try:
                tagged_users, tweet_query, time_span= parseTweet(tweet_from, tweet_text.lower())
            except:
                error_reply= "@%s please check the format of your tweet. I can't understand it yet!" % tweet_from
                error_reply_status= api.update_status(status=error_reply, in_reply_to_status_id=tweet_id)
            else:
                raw_data= getGoogleTrends(tweet_query, time_span)

                if "Interest over time" in raw_data:
                    timeseries_title, timeseries_data= parseGoogleData(raw_data)

                    outfile= open("tmp_data1.txt", "w")
                    outfile.write(raw_data)
                    outfile.close()

                    savePlotData(timeseries_title, timeseries_data tweet_id, tweet_from)


                elif "Check" in raw_data:
                    error_reply= "@%s please check the format of your date and keywords. I am finding it difficult to parse them." % tweet_from
                    error_reply_status= api.update_status(status=error_reply, in_reply_to_status_id=tweet_id)
                else:
                    error_reply= "@%s provided keywords have very less traffic to compare. Choose some interesting topics!" % tweet_from
                    error_reply_status= api.update_status(status=error_reply, in_reply_to_status_id=tweet_id)

    def on_error(self, status_code):
        print(status_code)
        return False


if __name__== "__main__":
    # twitter oauth
    auth = tweepy.OAuthHandler(config.twitter['API_Key'], config.twitter['API_Secret'])
    auth.set_access_token(config.twitter['Access_Token'],
                          config.twitter['Access_Token_Secret'])
    api = tweepy.API(auth)

    myStreamListener= MyStreamListener()
    myStream= tweepy.Stream(auth = api.auth, listener=myStreamListener)

    try:
        # starts listening to twitter stream
        #myStream.filter(track=['python'])
        #myStream.userstream(_with='user', replies='all')
        print("streamer not using")
    except Exception as e:
        print("Stream exception: %s" % e)
        raise e


    tweet_from= "pp"
    if tweet_from.lower() != MYUSERNAME:
        tweet_text= "hey @dora wanna find @ATwhoispopular samantha, tamanna 69m"
        tagged_users, tweet_query, time_span= parseTweet(tweet_from, tweet_text.lower())
        print(tagged_users)
        print(tweet_query)
        print(time_span)
        for i in range(10):
            raw_data= getGoogleTrends(tweet_query, time_span)
            print(raw_data== None)

