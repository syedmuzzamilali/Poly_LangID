import urllib.request
import re

url = 'https://aclanthology.org/W16-5803/'
try:
    with urllib.request.urlopen(url) as response:
        html = response.read().decode('utf-8')
        links = re.findall(r'href=[\'"]?([^\'" >]+)', html)
        zips = [link for link in links if link.endswith('.zip') or 'Attachment' in link]
        print(f"Swahili links: {zips}")
except Exception as e:
    print(f"Error: {e}")
