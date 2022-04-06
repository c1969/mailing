import os
import sqlite3

DATABASE_FLOW_1 = os.path.join("db/db.db")
DATABASE_FLOW_2 = os.path.join("db/qr.db")


class dbx():

    def __init__(self) -> None:
        pass

    def count_customers(self):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = """ select count(distinct costumer_name) from data_costumer """
            c.execute(sql)
            return c.fetchone()[0]

    def count_addresses(self):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = """ select count(*) from (select distinct firstname, lastname, company, street, number, zipcode, city from data_retailer) """
            c.execute(sql)
            return c.fetchone()[0]

    def count_swiss_addresses(self):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = """ select count(*) from (select distinct firstname, lastname, company, street, number, zipcode, city, country from data_retailer where upper(country) in ('SCHWEIZ', 'CH')) """
            c.execute(sql)
            return c.fetchone()[0]

    def count_addresses_from_swiss_customers(self):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = """ select count(*) from (select distinct firstname, lastname, company, street, number, zipcode, city, country from data_retailer where session_id in (select distinct session_id from data_costumer where upper(country) like 'CH')) """
            c.execute(sql)
            return c.fetchone()[0]

    def get_data_costumer(self):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = """ SELECT * FROM data_costumer order by costumer_name"""
            c.execute(sql)
            return c.fetchall()

    def get_data_retailer(self, session_id):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = """ SELECT distinct company, salutation, firstname, lastname, street, number, zipcode, city, country, id FROM data_retailer where session_id = ? order by company"""
            c.execute(sql, (session_id, ))
            return c.fetchall()

    def set_costumer_data(self, d):
        conn = sqlite3.connect(DATABASE_FLOW_1)
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
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sid = (sid, )
            sql = 'SELECT * FROM data_costumer WHERE session_id = ?'
            c.execute(sql, sid)
            return c.fetchall()
        else:
            return False

    def get_costumer_id(self):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = 'SELECT costumer_id FROM data_costumer'
            c.execute(sql)
            return c.fetchall()
        else:
            return False

    def set_retailer_data(self, d):
        conn = sqlite3.connect(DATABASE_FLOW_1)
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

    def get_retailer_by_qr(self, qr):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = 'SELECT * FROM data_retailer WHERE qr = ?'
            c.execute(sql, (qr, ))
            return c.fetchall()
        else:
            return False

    def get_dealer_for_retailer(self, sid):
        conn = sqlite3.connect(DATABASE_FLOW_1)
        if conn:
            c = conn.cursor()
            sql = 'SELECT * FROM data_costumer WHERE session_id = ?'
            c.execute(sql, (sid, ))
            return c.fetchall()
        else:
            return False

    def get_flipsnack_url(self, path):
        connection = sqlite3.connect(DATABASE_FLOW_1)
        if connection:
            cursor = connection.cursor()
            sql = 'select flipsnack_url from magalog_url where path = ?'
            cursor.execute(sql, (path, ))
            return cursor.fetchone()
        else:
            return False

    def insert_magalog_url(self, data):
        connection = sqlite3.connect(DATABASE_FLOW_1)
        if connection:
            cursor = connection.cursor()
            sql = "insert into magalog_url({}) values({})".format(
                ",".join(list(data.keys())),
                ",".join(list(["?"]*len(data))))
            cursor.execute(sql, tuple(data.values()))
            connection.commit()
            connection.close()
            return True
        else:
            return False

    def delete_customer(self, session_id):
        connection = sqlite3.connect(DATABASE_FLOW_1)
        if connection:
            cursor = connection.cursor()
            delete_addresses_sql = "delete from data_retailer where session_id = ?"
            delete_customer_sql = "delete from data_costumer where session_id = ?"
            cursor.execute(delete_addresses_sql, (session_id, ))
            cursor.execute(delete_customer_sql, (session_id, ))
            connection.commit()
            connection.close()
            return True
        else:
            return False

    def delete_address(self, id):
        connection = sqlite3.connect(DATABASE_FLOW_1)
        if connection:
            cursor = connection.cursor()
            sql = "delete from data_retailer where id = ?"
            cursor.execute(sql, (id, ))
            connection.commit()
            connection.close()
            return True
        else:
            return False


class dby():

    def __init__(self) -> None:
        pass

    def set_qr_feedback(self, d):
        conn = sqlite3.connect(DATABASE_FLOW_2)
        if conn:
            c = conn.cursor()
            sql = 'INSERT INTO mailing ({}) VALUES ({})'.format(
                ','.join(list(d.keys())),
                ','.join(list(['?']*len(d))))

            c.execute(sql, tuple(d.values()))
            conn.commit()
            conn.close()
            return True
        else:
            return False
