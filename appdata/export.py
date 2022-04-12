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

sql1 = """ select costumer_name, name, streetname, plz, city, email, phone, country, session_id, file_data, opt3 FROM (select * from data_costumer order by opt3 desc) group by session_id """
sql2 = """ SELECT company, salutation, firstname, lastname, street, number, zipcode, city, country, qr, url, division, address_supplement from (select * FROM data_retailer WHERE session_id = ? order by id desc) group by company, salutation, firstname, lastname, street, number, zipcode, city, country """
sql3 = """ SELECT COUNT(*) FROM (SELECT distinct company, salutation, firstname, lastname, street, number, zipcode, city, country FROM data_retailer) """


def get_retailer(session_id):
    cy = db1.cursor()
    cy.execute(sql2, (session_id, ))
    return cy.fetchall()


def getnow():
    now = datetime.now()
    return now.strftime("%Y_%m_%d-%H_%M")


def get_salutation(salutation, firstname, lastname, division):
    frau = "Frau"
    herr = "Herr"

    if is_not_blank(salutation) and is_not_blank(firstname) and is_not_blank(lastname):
        if frau == get_value(salutation):
            return f"Liebe {firstname} {lastname}"
        elif herr == get_value(salutation):
            return f"Lieber {firstname} {lastname}"

    if is_not_blank(salutation) and is_not_blank(firstname) and is_blank(lastname):
        if frau == get_value(salutation):
            return f"Liebe {firstname}"
        elif herr == get_value(salutation):
            return f"Lieber {firstname}"

    if is_not_blank(salutation) and is_blank(firstname) and is_not_blank(lastname):
        if frau == get_value(salutation):
            return f"Liebe Frau {lastname}"
        elif herr == get_value(salutation):
            return f"Lieber Herr {lastname}"

    if is_blank(salutation) and is_not_blank(firstname) and is_not_blank(lastname):
        return f"Liebe(r) {firstname} {lastname}"

    if is_blank(salutation) and is_not_blank(firstname) and is_blank(lastname):
        return f"Liebe(r) {firstname}"

    if is_blank(salutation) and is_blank(firstname) and is_not_blank(lastname):
        return f"Liebe Frau/Lieber Herr {lastname}"

    if is_blank(salutation) and is_blank(firstname) and is_blank(lastname) and is_not_blank(division):
        return f"Liebe Abteilung {division}"

    return "Liebe Teamplayer*innen"


def get_value(string):
    return str(string or '').strip()


def is_not_blank(string):
    return string and get_value(string)


def is_blank(string):
    return not is_not_blank(string)


cx = db1.cursor()
cx.execute(sql1)
rx = cx.fetchall()

cz = db1.cursor()
cz.execute(sql3)
rz = cz.fetchone()
print(rz[0])

wb = Workbook()
ws = wb.active
ws.title = "HAKRO Fachhändler"

now = getnow()
source_file = "static/export/export.xlsx"
target_file = f"static/export/export_{now}.xlsx"
wbx = load_workbook(filename=source_file)
ws = wbx['Tabelle1']
s = wbx.active

START_ROW = 2
MAX_ROW = int(rz[0]) + 1

ix = START_ROW
for i in rx:
    print(i)
    retailers = get_retailer(i[8])
    for r in retailers:
        s.cell(row=ix, column=1).value = i[8]   # session_id
        s.cell(row=ix, column=2).value = i[0]   # costumer_name
        s.cell(row=ix, column=3).value = i[1]   # name
        s.cell(row=ix, column=4).value = i[2]   # streetname
        s.cell(row=ix, column=5).value = i[3]   # plz
        s.cell(row=ix, column=6).value = i[4]   # city
        s.cell(row=ix, column=7).value = i[5]   # email
        s.cell(row=ix, column=8).value = i[6]   # phone
        s.cell(row=ix, column=9).value = i[9]   # file_data
        s.cell(row=ix, column=10).value = f'{i[8]}.pdf'  # file_logo
        s.cell(row=ix, column=11).value = i[7]  # country
        s.cell(row=ix, column=12).value = i[10]  # opt3
        # Kunden
        s.cell(row=ix, column=13).value = r[0]  # company
        s.cell(row=ix, column=14).value = get_salutation(
            salutation=r[1], firstname=r[2], lastname=r[3], division=r[11])  # salutation
        s.cell(row=ix, column=15).value = r[2]  # firstname
        s.cell(row=ix, column=16).value = r[3]  # lastname
        s.cell(row=ix, column=17).value = r[4]  # street
        s.cell(row=ix, column=18).value = r[5]  # number
        s.cell(row=ix, column=19).value = r[6]  # zipcode
        s.cell(row=ix, column=20).value = r[7]  # city
        s.cell(row=ix, column=21).value = r[8]  # country
        s.cell(row=ix, column=22).value = r[9]  # qr
        s.cell(row=ix, column=23).value = r[10]  # url
        s.cell(row=ix, column=23).value = r[11]  # division
        s.cell(row=ix, column=23).value = r[12]  # address supplement

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
        ix += 1

print("Saving workbook")
wbx.save(filename=target_file)

p = os.path.join('static', 'export')

print("Creating assets.zip")
output_1 = p + "/" + f'asstets_{now}'
shutil.make_archive(output_1, 'zip', os.path.join('static', 'upload'))

print("Creating db.zip")
output_2 = p + "/" + f'db_{now}'
shutil.make_archive(output_2, 'zip', os.path.join('db'))

print("Creating qr.zip")
output_3 = p + "/" + f'qr_{now}'
shutil.make_archive(output_3, 'zip', os.path.join('static', 'export', 'qr'))

# time.sleep(1)

#print("Creating all.zip")
#output_4 = p + "/" + f'all_{now}'
#shutil.make_archive(output_4, 'zip', os.path.join('static', 'export'))

print("Export finished")
