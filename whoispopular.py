import requests
import confidential
from pytrends.pyGTrends import pyGTrends
import tweepy
import matplotlib.pyplot as plt


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
    #print(time_axis)

    # area = [3.14159, 12.56636, 28.27431, 50.26544, 78.53975, 113.09724]
    # square = [1.0, 4.0, 9.0, 16.0, 25.0, 36.0]

    for i in range(len(timeseries_title)- 1):
        y_axis= [(a[i+1]) for a in timeseries_data]
        y_axis= ["0" if a==" " else a for a in y_axis]
        y_axis= [int(a) for a in y_axis]

        plt.plot(time_axis, y_axis, label=timeseries_title[i+1])


    plt.xlabel('Radius/Side')
    plt.ylabel('Area')
    plt.title('Area of Shapes')
    plt.legend()
    #plt.draw()
    plt.savefig("abc.png")

def parseData(raw_data):
    timeseries_data= raw_data[raw_data.find("Interest over time"): raw_data.find("\n\n\n")]
    timeseries_data= timeseries_data.split("\n")
    timeseries_data= timeseries_data[1:]
    timeseries_data= [a.split(",") for a in timeseries_data]

    timeseries_title= timeseries_data[0]
    timeseries_data= timeseries_data[1:]

    return timeseries_title, timeseries_data

if __name__== "__main__":
    tweet= "katy perry, jay z, beyonce, kanye west"
    tweet_keywords= len(tweet.split(","))

    raw_data= get_googleTrends(tweet)
    # print(raw_data)

    timeseries_title, timeseries_data= parseData(raw_data)

    # outfile= open("tmp_data.txt", "w")
    # outfile.write(raw_data)
    # outfile.close()

    plotData(timeseries_title, timeseries_data)

