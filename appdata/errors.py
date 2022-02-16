import os
import sqlite3

DATABASE = os.path.join("db/db.db")


class Errors():

    def __init__(self) -> None:
        pass

    def get_error(self, errorid):
        conn = sqlite3.connect(DATABASE)
        if conn:
            c = conn.cursor()
            sql = """ SELECT * FROM errors WHERE errorid = ? """
            c.execute(sql, (errorid, ))
            return c.fetchall()
        else:
            return 0