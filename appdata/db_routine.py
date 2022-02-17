import os
import sqlite3

DATABASE = os.path.join("db/db.db")

class dbx():

    def __init__(self) -> None:
        pass

    def get_data_costumer(self):
        conn = sqlite3.connect(DATABASE)
        if conn:
            c = conn.cursor()
            sql = """ SELECT * FROM data_costumer """
            c.execute(sql)
            return c.fetchall()

    def get_data_retailer(self):
        conn = sqlite3.connect(DATABASE)
        if conn:
            c = conn.cursor()
            sql = """ SELECT * FROM data_retailer """
            c.execute(sql)
            return c.fetchall()

    def set_costumer_data(self, d):
        conn = sqlite3.connect(DATABASE)
        if conn:
            c = conn.cursor()
            sql = 'INSERT INTO data_costumer ({}) VALUES ({})'.format(
            ','.join(list(d.keys())),
            ','.join(list(['?']*len(d))))

            c.execute(sql, tuple(d.values()))
            conn.commit()
            conn.close()
            return True
        else:
            return False

    def get_costumer_data(self, sid):
        conn = sqlite3.connect(DATABASE)
        if conn:
            c = conn.cursor()
            sid = (sid, )
            sql = 'SELECT * FROM data_costumer WHERE session_id = ?'
            c.execute(sql, sid)
            return c.fetchall()
        else:
            return False

    def get_costumer_id(self):
        conn = sqlite3.connect(DATABASE)
        if conn:
            c = conn.cursor()
            sql = 'SELECT costumer_id FROM data_costumer'
            c.execute(sql)
            return c.fetchall()
        else:
            return False

    def set_retailer_data(self, d):
        conn = sqlite3.connect(DATABASE)
        if conn:
            c = conn.cursor()
            sql = 'INSERT INTO data_retailer ({}) VALUES ({})'.format(
            ','.join(list(d.keys())),
            ','.join(list(['?']*len(d))))

            c.execute(sql, tuple(d.values()))
            conn.commit()
            conn.close()
            return True
        else:
            return False
