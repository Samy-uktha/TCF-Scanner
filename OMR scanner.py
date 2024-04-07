import cv2
import numpy as np
import csv
import pandas as pd
import pytesseract
from tabulate import tabulate
import io
import os
from pdf2image import convert_from_path
from google.cloud import vision
from google.cloud import vision_v1
from google.cloud.vision_v1 import types

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'tcf-scanner-ccb138d4a9c9.json'
client = vision.ImageAnnotatorClient()

img_paths = []
images = convert_from_path("e1.pdf", output_folder="extracted_images", fmt="png")
for file in os.listdir("extracted_images"):
    path = os.path.join("extracted_images", file)
    img_paths.append(path)

#img = cv2.imread(img_paths[0])

coursecodes = []

def processOMRSheet(img):
    def getData(img):
        scale_factor = 1
        image = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)[1]

        course_name = thresh[450:488, 295:1542]
        faculty_name = thresh[511:550, 295:1542]
        course_code = thresh[671:953, 297:753]
        batch = thresh[626:953, 780:1041]
        slot = thresh[634:841, 1092:1350]
        qbox1 = thresh[1106:1270, 1350:1565]
        qbox2 = thresh[1358:1524, 1347:1568]
        qbox3 = thresh[1523:1690, 1348:1567]
        qbox4 = thresh[1777:1943, 1348:1567]

        return course_name, course_code, faculty_name, batch, slot, qbox1, qbox2, qbox3, qbox4

    def getPixelArray(img, r, c):
        height, width = img.shape
        h = height // r
        w = width // c
        rows = []
        boxes = []
        for i in range(r):
            rows.append(img[(i * h):((i + 1) * h), :])

        for row in rows:
            for i in range(c):
                boxes.append(row[:, (i * w):((i + 1) * w)])

        pixels = np.zeros((r, c))
        countC = 0
        countR = 0
        for image in boxes:
            totalPixels = cv2.countNonZero(image)
            pixels[countR][countC] = totalPixels
            countC += 1
            if countC == c:
                countR += 1
                countC = 0
        return pixels

    course_name, course_code, faculty_name, batch, slot, qbox1, qbox2, qbox3, qbox4 = getData(img)

    course_pixels = getPixelArray(course_code, 10, 6)
    batch_pixels = getPixelArray(batch, 5, 1)
    slot_pixels = getPixelArray(slot, 4, 2)
    qbox1_pixels = getPixelArray(qbox1, 5, 5)
    qbox2_pixels = getPixelArray(qbox2, 5, 5)
    qbox3_pixels = getPixelArray(qbox3, 5, 5)
    qbox4_pixels = getPixelArray(qbox4, 5, 5)

    course_pixels_trans = course_pixels.transpose(1, 0)
    reference = np.array([
        ['C', 'C', 'C', 'E', 'H', 'M', 'M', 'P', 'I', 'G'],
        ['E', 'S', 'Y', 'E', 'S', 'A', 'E', 'H', 'D', 'N'],
        ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
        ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
        ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
        ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    ])

    code = []
    courseCode = ""
    for i in range(6):
        row = course_pixels_trans[i]
        for element in row:
            if element > 200:
                code.append(list(row).index(element))
    for i in range(6):
        index = code[i]
        courseCode += reference[i][index]

    #coursecodes.append(courseCode)

    batch_reference = [1,2,3,4,5]
    #print(batch_pixels)
    batch = "null"
    for pix in batch_pixels:
        if pix > 600:
            index = list(batch_pixels).index(pix)
            batch = batch_reference[index]

    code = []
    pixlist = []
    slot_reference = ['A', 'E', 'B', 'F', 'C', 'G', 'D', 'H']
    # print(slot_pixels)
    for i in range(4):
        row = slot_pixels[i]
        for element in row:
            pixlist.append(element)
    slot = "null"
    for element in pixlist:
        if element > 300:
            index = pixlist.index(element)
            slot = slot_reference[index]



    def getAnswers(pixels):
        ref = ['SA', 'A', 'N', 'D', 'SD']
        point = [10,8,6,4,2]
        pix = []
        answers = []
        points = []
        for i in range(5):
            row = pixels[i]
            for element in row:
                if element > 200:
                    pix.append(list(row).index(element))
        for i in range(5):
            index = pix[i]
            answers.append(ref[index])
            points.append(point[index])
        return answers, points

    answers1, points1 = getAnswers(qbox1_pixels)
    answers2, points2 = getAnswers(qbox2_pixels)
    answers3, points3 = getAnswers(qbox3_pixels)
    answers4, points4 = getAnswers(qbox4_pixels)

    OMRanswers = answers1 + answers2 + answers3 + answers4
    OMRpoints = points1 + points2 + points3 + points4



    #return courseCode, slot, OMRanswers
    if courseCode not in coursecodes:
        header = ["q no.","average","median","standard deviation", "points"]
        data = []

        for i in range(20):
            row = [i + 1,0,0,0, OMRpoints[i]]
            data.append(row)

        data = pd.DataFrame(data, columns=header)
        csv_path = f"OMR_{courseCode}-{batch}.csv"
        data.to_csv(csv_path, index=False)
        coursecodes.append(courseCode)

    elif courseCode in coursecodes:
        with open(f"OMR_{courseCode}-{batch}.csv", 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            rows[0].append("points")
        for row in rows[1:]:
            indx = rows.index(row)
            row.append(OMRpoints[indx-1])
            #rowAvg = sum(row[4:]) / len(row[4:])
            #row[1] = rowAvg

        for row in rows[1:]:
            rowfl = [float(value) for value in row]
            row[1] = sum(rowfl[4:]) / len(rowfl[4:])
            values = []
            for value in rowfl:
                values.append(value)
            values.sort()
            n = len(values)
            if n%2 ==0:
                median = (values[n//2]+values[n//2+1]) /2
            else:
                median = values[n//2+1]
            row[2] = median



        with open(f"OMR_{courseCode}-{batch}.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)




    print(f"\nfollowing feedback given for course {courseCode} in slot {slot}\n")
    #print(tabulate(data, header))
    #print("data has been stored in csv file!!")
    #print(f"the score for this instructor is {score}/200")


def processTextSheet(img):

    def readImg(img):
        content = cv2.imencode(".jpg", img)[1].tobytes()
        image = vision_v1.types.Image(content=content)
        response = client.document_text_detection(image=image)
        texts = response.full_text_annotation.text
        return texts
    coursecode = readImg(img[512:563,350:598])
    coursecode = ''.join(char for char in coursecode if (char.isalpha() or char.isdigit()))
    coursetitle = readImg(img[516:571,916:1565])
    semester = readImg(img[583:649,303:681])
    faculty = readImg(img[572:631,856:1442])
    faculty = ''.join(char for char in faculty if char.isalpha())

    # scale_factor = 1
    # image = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # thresh = cv2.threshold(gray, 205, 255, cv2.THRESH_BINARY_INV)[1]
    #
    # coursecode = pytesseract.image_to_string(thresh[512:563,350:598],config ="--psm 6")
    # coursecode = ''.join(char for char in coursecode if (char.isalpha() or char.isdigit()))
    # coursetitle = pytesseract.image_to_string(thresh[516:571,916:1565],config="--psm 6")
    # semester = pytesseract.image_to_string(thresh[583:649,303:681],config="--psm 6")
    # faculty = pytesseract.image_to_string(thresh[572:631,856:1442],config="psm 6")
    # faculty = ''.join(char for char in faculty if char.isalpha())


    qbox1 = img[726:956,88:1597]
    qbox2 = img[1001:1232,88:1597]
    qbox3 = img[1281:1510,88:1597]
    qbox4 = img[1558:1781,88:1597]
    qbox5 = img[1837:2115,88:1597]

    qboxes = [qbox1,qbox2,qbox3,qbox4,qbox5]
    aboxes = []

    for box in qboxes:
        content = cv2.imencode(".jpg",box)[1].tobytes()
        image = vision_v1.types.Image(content=content)
        response = client.document_text_detection(image=image)
        texts = response.full_text_annotation.text
        aboxes.append(texts)
        # with io.open(box, 'rb') as image_file:
        #     content = image_file.read()
        #
        # image = vision_v1.types.Image(content=content)
        # response = client.document_text_detection(image=image)
        #
        # answer = response.full_text_annotation.text
        # # answer = pytesseract.image_to_string(box, config="--psm 6")
        # aboxes.append(answer)


    header = ["q no.", "answers"]
    data = []
    for i in range(5):
        row = [i + 1, aboxes[i]]
        data.append(row)
    data = pd.DataFrame(data, columns=header)
    print(f"following feedback given for course {coursecode}-{coursetitle} taken by {faculty} in semester {semester}\n")
    print(tabulate(data, header))
    csv_path = f"Text_{faculty}-{coursecode}.csv"
    data.to_csv(csv_path, index=False)
    print("data has been stored in csv file!!")



# for image in img_paths:
#     img = cv2.imread(image)
#     processOMRSheet(img)

#img = cv2.imread(img_paths[0])
#processOMRSheet(img)

img = cv2.imread("text0.png")
processTextSheet(img)
