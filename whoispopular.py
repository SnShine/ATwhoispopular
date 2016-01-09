import requests
import confidential, sg_filter
from pytrends.pyGTrends import pyGTrends
import tweepy
import matplotlib.pyplot as plt
import numpy as np


def get_googleTrends(searchterms, period= None):
    google_username= confidential.username
    google_password= confidential.password

    print("Connecting to google")
    connector = pyGTrends(google_username, google_password)

    connector.request_report(keywords= searchterms, date= period)
    data= connector.get_data()

    if "An error has been detected" in data:
        print("Check the format of your date and keywords.")
    elif "Interest over time" in data:
        return data
    else:
        print("Provided keywords have less traffic to compare.")

def plotData(timeseries_title, timeseries_data):
    # plt.plot(radius, square, marker='o', linestyle='--', color='r', label='Square')

    time_axis= [i+1 for i in range(len(timeseries_data))]

    #custom x labels
    time_ticks_diff= int(len(timeseries_data)/5)
    time_ticks= [1, time_ticks_diff, 2*time_ticks_diff, 3*time_ticks_diff, 4*time_ticks_diff, len(timeseries_data)-1]
    print(time_ticks)
    time_labels= [timeseries_data[a][0] for a in time_ticks]
    #change latest
    if timeseries_title[0]== "Time":
        time_labels[-1]= "Now"
    elif timeseries_title[0]== "Day":
        time_labels[-1]= "Today"
    else:
        time_labels[-1]= "This week"

    print(time_labels)

    plt.xticks(time_ticks, time_labels)

    for i in range(len(timeseries_title)- 1):
        y_axis= [(a[i+1]) for a in timeseries_data]
        y_axis= ["0" if a==" " else a for a in y_axis]
        y_axis= [int(a) for a in y_axis]
        y_axis_smooth= sg_filter.savitzky_golay(y_axis, 11, 3)

        #plt.plot(time_axis, y_axis, linewidth=2, c="purple")
        plt.plot(time_axis, y_axis_smooth, linewidth=2, linestyle="-", label=timeseries_title[i+1])



    plt.xlabel(timeseries_title[0])
    # plt.ylabel('Area')
    plt.title('By @SnShines')
    plt.legend()
    #plt.draw()

    current_fig= plt.gcf()
    current_fig.set_size_inches(18.5, 10.5)


    current_fig.savefig("abc.png")

def parseData(raw_data):
    timeseries_data= raw_data[raw_data.find("Interest over time"): raw_data.find("\n\n\n")]
    timeseries_data= timeseries_data.split("\n")
    timeseries_data= timeseries_data[1:]
    timeseries_data= [a.split(",") for a in timeseries_data]

    timeseries_title= timeseries_data[0]
    timeseries_data= timeseries_data[1:]

    return timeseries_title, timeseries_data

if __name__== "__main__":
    tweet= "artificial intelligence, machine learning"
    tweet_keywords= len(tweet.split(","))

    raw_data= get_googleTrends(tweet, "today 2-d")
    #raw_data= get_googleTrends(tweet)

    if raw_data is not None:
        timeseries_title, timeseries_data= parseData(raw_data)

        outfile= open("tmp_data1.txt", "w")
        outfile.write(raw_data)
        outfile.close()

        plotData(timeseries_title, timeseries_data)

