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

sql1 = """ select costumer_name, name, streetname, plz, city, email, phone, country, session_id, file_data, opt3 FROM (select * from data_costumer order by opt3 desc) where session_id in ('ff879b8c-1107-495d-a8ec-8b825e3c50b5', '1668f6e3-efa6-471a-a7b1-53a75af6bf5a', '585250f7-314b-4332-a4dd-3b2d70d94870', 'fbf81322-d755-4207-8ab0-86ae5e779394', '742bc47f-d243-4ca9-83bf-68e1456c0d63', '2bebf0df-5bef-4138-a783-7a2d319cfd32', 'b3bdd455-7ca1-45d7-aacb-9332255cfbbf', '7fe9f2e8-4c67-42a4-a014-ceff22bcb4f5', 'd8cd15b9-caf6-40f9-9673-d152d99ff095', '3f7ed229-6a07-4a70-95c8-22dfe18b537d', '57710344-6baf-4632-9dcc-3446d7d1ca2d', '791890f9-8aa9-4b8a-a642-6d47f662f182', '213eb5db-849d-44b6-95db-e0f10d416f56', 'a58a0f77-3ed0-4b1c-afac-51f65096cb79', '9904e441-4d96-45af-bb08-d66580ad3dd5', '52847d1c-2c01-4714-9cfa-c58fec982c39', '6136eefa-da33-4b17-837b-9446fbe53345', '3f30954b-5fe3-4f08-8aac-60e0a508f769', '5a28a7fa-ad72-4321-a8c3-348de20b43ba', '3e580a87-8c19-4945-9fd1-85d893121859', '139a2a55-5ae1-4355-85ca-5ac457324e8a', 'adf78fc8-0734-414b-bfea-aeb6ad5c26df', 'b1aa0d43-58f8-4403-907e-8b168f35d251', 'b5269148-1f9f-460d-b8c4-ef9d0512a88b', '53c1d806-533f-489c-9a84-1f94f933dcb8', '27468fcc-1cbf-4cef-ad09-506fbc609dd6', '90bfa967-8351-456e-9282-69aa183283dc', '5e34f654-8177-4de0-b17d-7ade7d7c6e7b', 'd860da26-8c4d-40e0-b669-59cd54a23070', '57204962-bc21-47ac-b292-cee7dc0a8fcf', '9c9834d0-a213-4fa8-98d8-35a067546dbd', '32f6d560-5d86-4f84-95d7-53e960d8689e', '44d8d119-a071-48c1-9ae7-16155bbaacb0', 'd9b977c5-5c2b-41fe-a870-040188bb3355', 'b9ef6552-68a8-45c7-94f6-d98173fa8ad6', 'cc079f24-6c52-4bcd-ae29-4d1205b79af3', '88e03ffe-ad73-41d1-a524-054f1fc3273e', '8e7ce254-1e07-418b-8692-ad3ec9db8f25', '09da016b-a160-49d0-b0f3-7b2e22f42b9f', 'fb3fc75e-e14a-471e-bcf6-5aa99c148ffa', '3e9a8dd1-c698-4ec8-8ba3-c31a5c745ecd', '021603b4-887a-4ae5-b1af-24be61fd31bc', '1a53f9fb-e586-4007-9e31-3d5c1a54952c', '69cd58fd-3188-4a1d-b69e-964e0d2e0da4', '8593fd21-d9f3-4a22-a05b-0e1f2a662a99', 'bd8a51cb-0c62-4f57-897a-aec468ca4961', '81df069a-b3ae-4ed0-b378-af560e309b1f', 'b937e189-3b33-4bb3-a055-a7fca6301dde', '8f6af8a6-0ad2-4efd-84bb-b41955d9ee9a', '09d45f64-526d-4202-a4ec-98457571e8e1', '49b152c5-ff41-4f1d-a384-966d712ac68e', 'c781f0e9-b5cc-4567-8f4e-9b74a495c1b1', '9504702c-c062-48be-af0a-c0758a93e68e', '731e5800-54db-400f-b9a6-af6e72333858', '19196167-68d2-4cfe-b269-c34d7365de98', '78faac27-8b80-4e43-9550-9a8fbb4aa265', 'a4b379d1-42c1-4964-b86a-1785414c8c75') group by session_id """
sql2 = """ SELECT company, salutation, firstname, lastname, street, number, zipcode, city, country, qr, url from (select * FROM data_retailer WHERE session_id = ? order by id desc) group by company, salutation, firstname, lastname, street, number, zipcode, city, country """
sql3 = """ SELECT COUNT(*) FROM (SELECT distinct company, salutation, firstname, lastname, street, number, zipcode, city, country FROM data_retailer) """


def get_retailer(session_id):
    cy = db1.cursor()
    cy.execute(sql2, (session_id, ))
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
ws = wb.active
ws.title = "HAKRO Fachhändler"

source_file = "static/export/export.xlsx"
target_file = f"static/export/export_{getnow()}.xlsx"
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
        s.cell(row=ix, column=12).value = i[10] # opt3
        # Kunden
        s.cell(row=ix, column=13).value = r[0]  # company
        s.cell(row=ix, column=14).value = "Liebe Teamplayer*innen" #r[1]  # salutation
        s.cell(row=ix, column=15).value = r[2]  # firstname
        s.cell(row=ix, column=16).value = r[3]  # lastname
        s.cell(row=ix, column=17).value = r[4]  # street
        s.cell(row=ix, column=18).value = r[5]  # number
        s.cell(row=ix, column=19).value = r[6]  # zipcode
        s.cell(row=ix, column=20).value = r[7]  # city
        s.cell(row=ix, column=21).value = r[8]  # country
        s.cell(row=ix, column=22).value = r[9]  # qr
        s.cell(row=ix, column=23).value = r[10] # url

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
output_1 = p + "/" + f'asstets_{getnow()}'
shutil.make_archive(output_1, 'zip', os.path.join('static', 'upload'))

print("Creating db.zip")
output_2 = p + "/" + f'db_{getnow()}'
shutil.make_archive(output_2, 'zip', os.path.join('db'))

print("Creating qr.zip")
output_3 = p + "/" + f'qr_{getnow()}'
shutil.make_archive(output_3, 'zip', os.path.join('static', 'export', 'qr'))

time.sleep(1)

print("Creating all.zip")
output_4 = p + "/" + f'all_{getnow()}'
shutil.make_archive(output_4, 'zip', os.path.join('static', 'export'))

print("Export finished")