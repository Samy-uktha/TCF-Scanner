from docxtpl import DocxTemplate
import csv
doc = DocxTemplate("report.docx")
avg = []
med = []
std = []
d = {}
file = csv.reader(open("OMR_CS2210-1.csv", 'r'))
rows = []
for row in file:
    rows.append(row)
for i in range(1,len(rows)):
    avg.append(round(float(rows[i][1]),3))
    med.append(round(float(rows[i][2]),3))
    std.append(round(float(rows[i][3]),3))
for i in range(len(rows)):
    d[f'a{i}0a'] = avg[i-1]
    d[f'a{i}1a'] = med[i-1]
    d[f'a{i}2a'] = std[i-1]
context = d
doc.render(context)
doc.save("generated_doc.docx")