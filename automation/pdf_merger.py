import PyPDF2
import sys
import os

merger = PyPDF2.PdfFileMerger()
counter = 0
for file in os.listdir(os.curdir):
    if file.endswith('.pdf'):
        counter +=1 
        merger.append(file)
if counter == 0:
    print('No PDFs found in the current directory')
else:
    merger.write('Leo_Rozanov_DPF-Pheno_travel_receipts.pdf')
    