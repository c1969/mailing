'''
Diese Script zipped den Upload-Ordner für den Drucker/Sigloch
Nach dem Zippen bitte das Zip File kopieren
'''

import os
import shutil
import sqlite3
import qrcode
import openpyxl
import time
from openpyxl import Workbook, load_workbook
from datetime import datetime
from time import strftime

db1 = sqlite3.connect("db/db.db")

sql1 = """ SELECT * FROM data_costumer """
sql2 = """ SELECT * FROM data_retailer WHERE session_id = ? """
sql3 = """ SELECT COUNT(*) FROM data_retailer """

def get_retailer(sid):
    cy = db1.cursor()
    cy.execute(sql2, (sid, ))
    return cy.fetchall()

def getnow():
    now = datetime.now()
    return now.strftime("%Y_%m_%d-%H_%M")

cx = db1.cursor()
cx.execute(sql1)
rx = cx.fetchall()

cz = db1.cursor()
cz.execute(sql3)
rz = cz.fetchone()
print(rz[0])

wb = Workbook()
ws =  wb.active
ws.title = "HAKRO Fachhändler"

source_file = "static/export/export.xlsx"
target_file = f"static/export/export_{getnow()}.xlsx"
wbx = load_workbook(filename = source_file)
ws = wbx['Tabelle1']
s = wbx.active

START_ROW = 2
MAX_ROW = int(rz[0]) + 1

ix = START_ROW
for i in rx:
    print(i)
    retailers = get_retailer(i[1])
    for r in retailers:
        s.cell(row=ix, column=1).value = i[1]
        s.cell(row=ix, column=2).value = i[2]
        s.cell(row=ix, column=3).value = i[4]
        s.cell(row=ix, column=4).value = i[5]
        s.cell(row=ix, column=5).value = i[6]
        s.cell(row=ix, column=6).value = i[7]
        s.cell(row=ix, column=7).value = i[8]
        s.cell(row=ix, column=8).value = i[9]
        s.cell(row=ix, column=9).value = i[10]
        s.cell(row=ix, column=10).value = f'{i[1]}.pdf'
        s.cell(row=ix, column=11).value = i[16]
        s.cell(row=ix, column=12).value = i[14]
        #Kunden
        s.cell(row=ix, column=13).value = r[4]
        s.cell(row=ix, column=14).value = r[2]
        s.cell(row=ix, column=15).value = r[3]
        s.cell(row=ix, column=16).value = r[5]
        s.cell(row=ix, column=17).value = r[6]
        s.cell(row=ix, column=18).value = r[7]
        s.cell(row=ix, column=19).value = r[8]
        s.cell(row=ix, column=20).value = r[9]
        s.cell(row=ix, column=21).value = r[10]
        
        print(r)
        qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=15,
        border=1,
        )
        qr.add_data(f'{r[10]}')
        qr.make(fit=True)
        qr_filename = os.path.join('static', 'export', 'qr', f'{r[9]}.png')
        qr_code = qr.make_image(fill_color="black", back_color="white")
        qr_code.save(qr_filename)
        ix+=1
wbx.save(filename=target_file)

p = os.path.join('static', 'export')

output_1 = p + "/" + f'asstets_{getnow()}'
shutil.make_archive(output_1, 'zip', os.path.join('static', 'upload'))

output_2 = p + "/" + f'db_{getnow()}'
shutil.make_archive(output_2, 'zip', os.path.join('db'))

output_3 = p + "/" + f'qr_{getnow()}'
shutil.make_archive(output_3, 'zip', os.path.join('static', 'export', 'qr'))

time.sleep(1)

output_4 = p + "/" + f'all_{getnow()}'
shutil.make_archive(output_4, 'zip', os.path.join('static', 'export'))