import io
import os
import pandas as pd
import csv
from google.cloud import vision
from google.cloud import vision_v1
from google.cloud.vision_v1 import types

os.environ['GOOGLE_APPLICATION_CREDENTIALS']=r'tcf-scanner-ccb138d4a9c9.json'
client = vision.ImageAnnotatorClient()

bounds = []

file_name = os.path.abspath('text0.png')
with io.open(file_name,'rb') as image_file:
    content = image_file.read()

image = vision.Image(content = content)
response = client.document_text_detection(image=image)
document = response.full_text_annotation



# image = vision_v1.types.Image(content=content)
# response = client.document_text_detection(image=image)
# docText = response.full_text_annotation.text

print(docText)



# pages = response.full_text_annotation.pages
# for page in pages:
#     for block in page.blocks:
#         print('block confidence:', block.confidence)
#
#         for paragraph in block.paragraphs:
#             print('paragraph confidence:', paragraph.confidence)
#
#             for word in paragraph.words:
#                 word_text = ''.join([symbol.text for symbol in word.symbols])
#
#                 print('Word text: {0} (confidence: {1}'.format(word_text, word.confidence))
#
#                 for symbol in word.symbols:
#                     print('\tSymbol: {0} (confidence: {1}'.format(symbol.text, symbol.confidence))