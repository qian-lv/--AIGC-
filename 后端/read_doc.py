from docx import Document

doc = Document('D:\\OneDrive\\Desktop\\food_app\\项目计划书（新）.docx')

for para in doc.paragraphs:
    print(para.text)