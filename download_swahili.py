import urllib.request
import zipfile
import io
import os

print('Downloading Swahili dataset...')
url = 'https://aclanthology.org/attachments/W16-5803.Attachment.zip'
try:
    with urllib.request.urlopen(url) as response:
        with zipfile.ZipFile(io.BytesIO(response.read())) as z:
            z.extractall('datasets/swahili_english_raw')
            print('Extracted Swahili dataset.')
except Exception as e:
    print(f"Failed to download Swahili: {e}")
