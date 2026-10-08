import urllib.request
import re

url = 'https://data.mendeley.com/datasets/pn6xjx4zkd/1'
try:
    with urllib.request.urlopen(url) as response:
        html = response.read().decode('utf-8')
        links = re.findall(r'href=[\'"]?([^\'" >]+)', html)
        print("Mendeley Links:", links)
except Exception as e:
    print(e)
