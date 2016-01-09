import requests
import confidential

print(confidential.username)

URL= "http://www.google.com/trends/fetchComponent?hl=en-US&q=html5,jquery&cid=TIMESERIES_GRAPH_0&export=5&w=500&h=300"
r= requests.get(URL)
out_file= open("page.html", "w")
out_file.write(r.text)
out_file.close()

print(r.status_code)
