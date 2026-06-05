import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
     "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def execute(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()

def fetch_one(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    finally:
        conn.close()


def fetch_all(sql, params=None):
    conn = get_conn()
    try :
        with conn.cursor() as cursor:
            cursor.execute(sql,params)
            return cursor.fetchall()
    finally:
        conn.close()

