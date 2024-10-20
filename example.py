#Importing Libraries
#Importing Google Text to Speech library
from gtts import gTTS

#Importing PDF reader PyPDF2
import PyPDF2

if 1> 2:
   1+1
elif 2>3:
   2+2
   a = 5
else:
   print('hello')

if 'moo' == 'shoo':
   1+1+1


a = [x+2+x for x in range(10)]
#Open file Path
pdf_File = open('name.pdf', 'rb') 

#Create PDF Reader Object
pdf_Reader = PyPDF2.PdfFileReader(pdf_File)
count = pdf_Reader.numPages # counts number of pages in pdf
textList = []

#Extracting text data from each page of the pdf file
for i in range(count):
   try:
    a= 5
    page = pdf_Reader.getPage(i)    
    textList.append(page.extractText())
   except:
       pass

#Converting multiline text to single line text
textString = " ".join(textList)

print(textString)

#Set language to english (en)
language = 'en'

#Call GTTS
myAudio = gTTS(text=textString, lang=language, slow=False)

#Save as mp3 file
myAudio.save("Audio.mp3")