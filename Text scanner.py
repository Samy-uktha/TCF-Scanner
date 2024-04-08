import io
import os
import pandas as pd
import csv
from google.cloud import vision
from google.cloud import vision_v1
from google.cloud.vision_v1 import types

os.environ['GOOGLE_APPLICATION_CREDENTIALS']=r'tcf-scanner-ccb138d4a9c9.json'
client = vision.ImageAnnotatorClient()

file_name = os.path.abspath('sem.jpg')
with io.open(file_name,'rb') as image_file:
    content = image_file.read()
image = vision_v1.types.Image(content=content)
response = client.document_text_detection(image=image)
texts = response.full_text_annotation.text
print(texts)
words = []
word = ""
for alphabet in texts:
    if alphabet.isalpha():
        word += alphabet
    elif alphabet == ".":
        word += "\n"
    else:
        word += " "
print(word)
