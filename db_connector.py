# Module Imports
from fileinput import close

import mariadb
import sys
from dotenv import load_dotenv
import os

load_dotenv()

USER = os.getenv('MARIADB_USER')
PASSWORD = os.getenv('MARIADB_PASSWORD')
URL = os.getenv('MARIADB_URL')
DB = os.getenv('MARIADB_DB')
PORT = int(os.getenv('MARIADB_PORT'))


def make_connection():
    # Connect to MariaDB Platform
    try:
        conn = mariadb.connect(
            user=USER,
            password=PASSWORD,
            host=URL,
            port=PORT,
            database=DB

        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    return conn


def count_lines(conn):
    # Get Cursor
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM links")
    count, = cur.fetchone()
    print(f"COUNT: {count}")
    return count


def insert_into_db(conn, uploader, file_url):
    # Get Cursor
    cur = conn.cursor()
    print(uploader)
    try:
        cur.execute("INSERT INTO links (uploader,url) VALUES (?, ?)", (uploader, file_url))
        print("Successfully inserted!")
    except mariadb.Error as e:
        print(f"Error: {e}")


def get_link(conn, number):
    number -= 1
    cur = conn.cursor()
    cur.execute(f"SELECT url FROM links order by id offset ? rows fetch first row only", (number,))
    link, = cur.fetchone()
    print(link)
    return link


def commit(conn):
    conn.commit()


def close_connection(conn):
    conn.close()
