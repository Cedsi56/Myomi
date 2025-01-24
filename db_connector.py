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

DAILY_PULLS=10


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


def count_lines_user(conn, uploader):
    # Get Cursor
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM links where uploader = ?", (uploader,))
    count, = cur.fetchone()
    print(f"COUNT: {count}")
    return count


def insert_into_db(conn, uploader, file_url, star_rating=1):
    # Get Cursor
    cur = conn.cursor()
    print(uploader)
    try:
        cur.execute("INSERT INTO links (uploader,url,star_rating) VALUES (?, ?, ?)", (uploader, file_url, star_rating))
        print("Successfully inserted!")
    except mariadb.Error as e:
        print(f"Error: {e}")


def get_link(conn, number):
    number -= 1
    cur = conn.cursor()
    cur.execute(f"SELECT url, uploader, star_rating FROM links order by id offset ? rows fetch first row only", (number,))
    link, uploader, star = cur.fetchone()
    print(link)
    return link, uploader, star


def get_link_user(conn, number, user):
    number -= 1
    cur = conn.cursor()
    cur.execute(f"SELECT url, star_rating FROM links WHERE uploader = ? order by id offset ? rows fetch first row only", (user, number))
    link, star = cur.fetchone()
    print(link)
    return link, star


def get_next_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT `auto_increment` FROM INFORMATION_SCHEMA.TABLES WHERE table_name = 'links'")
    next_id, = cur.fetchone()
    print(next_id)
    return next_id


def insert_user(conn, user):
    # Get Cursor
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (id, current_pity, current_4star_pity, essence) VALUES (?, ?, ?, ?)",
                    (user, 0, 0, 0))
        print("Successfully inserted user!")
        conn.commit()
    except mariadb.Error as e:
        print(f"Error: {e}")


def reset_pulls(conn, user):
    # Get Cursor
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET pulls = ?, last_pull = CURRENT_DATE() WHERE id = ?", (DAILY_PULLS, user))
        print("Successfully inserted user!")
        conn.commit()
    except mariadb.Error as e:
        print(f"Error: {e}")


def get_user(conn, user):
    cur = conn.cursor()
    cur.execute(f"SELECT pulls, last_pull, current_pity, current_4star_pity, essence "
                f"FROM users WHERE id = ? order by id fetch first row only", (user,))
    res = cur.fetchone()
    if res is None:
        # insert in db
        insert_user(conn, user)
        pulls, last_pull, current_pity, current_4star_pity, essence = get_user(conn, user)
    else:
        pulls, last_pull, current_pity, current_4star_pity, essence = res
    return pulls, last_pull, current_pity, current_4star_pity, essence


def count_lines_rarity(conn, rarity):
    # Get Cursor
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM links where star_rating = ?", (rarity,))
    count, = cur.fetchone()
    print(f"COUNT: {count}")
    return count


def get_link_rarity(conn, number, rarity):
    number -= 1
    cur = conn.cursor()
    cur.execute(f"SELECT url, star_rating, id FROM links WHERE star_rating = ? order by id offset ? rows "
                f"fetch first row only", (rarity, number))
    link, star, link_id = cur.fetchone()
    print(link)
    return link, star, link_id


def check_user_already_has(conn, user, link):
    # Get Cursor
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM user_waifu where user_id = ? and link_id = ?", (user, link))
    count, = cur.fetchone()
    return count != 0


def register_pull(conn, user, link):
    # Get Cursor
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO user_waifu (user_id, link_id) VALUES (?, ?)",
                    (user, link))
        print("Successfully inserted into user_waifu!")
        conn.commit()
    except mariadb.Error as e:
        print(f"Error: {e}")


def lose_pull(conn, user, pulls):
    # Get Cursor
    cur = conn.cursor()
    pulls -= 1
    try:
        cur.execute("UPDATE users SET pulls = ? where id = ?",
                    (pulls, user))
        conn.commit()
    except mariadb.Error as e:
        print(f"Error: {e}")


def set_essence(conn, user, essence):
    # Get Cursor
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET essence = ? where id = ?",
                    (essence, user))
        conn.commit()
    except mariadb.Error as e:
        print(f"Error: {e}")


def update_pity(conn, user, pity_4, pity_5):
    # Get Cursor
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET current_4star_pity = ?, current_pity = ? where id = ?",
                    (pity_4, pity_5, user))
        conn.commit()
    except mariadb.Error as e:
        print(f"Error: {e}")


def get_link_dex(conn, number, user):
    number -= 1
    cur = conn.cursor()
    cur.execute(f"SELECT url, uploader, star_rating FROM links INNER JOIN user_waifu uw on links.id = uw.link_id "
                f"WHERE uw.user_id = ? order by star_rating desc, id offset ? rows fetch first row only",
                (user, number))
    link, uploader, star = cur.fetchone()
    print(link)
    return link, uploader, star


def count_lines_dex(conn, user):
    # Get Cursor
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(1) FROM links INNER JOIN user_waifu uw on links.id = uw.link_id "
                f"WHERE uw.user_id = ? order by star_rating desc, id",
                (user,))
    count, = cur.fetchone()
    print(f"COUNT: {count}")
    return count


def get_essence_count(conn, user):
    # Get Cursor
    cur = conn.cursor()
    cur.execute("SELECT essence FROM users where id = ?", (user,))
    essence_count, = cur.fetchone()
    print(f"ESSENCE COUNT: {essence_count}")
    return essence_count


def get_all_link_rarity_unobtained(conn, rarity, user):
    print(f"rarity : {rarity}")
    print(f"user : {user}")
    cur = conn.cursor()
    cur.execute("select id, url from links WHERE star_rating = ? EXCEPT select id, url from links "
                "INNER JOIN user_waifu uw on links.id = uw.link_id WHERE uw.user_id = ? AND star_rating = ?",
                (rarity, user, rarity))
    link_ids = [(link, url) for link, url in cur]
    print(link_ids)
    return link_ids


def commit(conn):
    conn.commit()


def close_connection(conn):
    conn.close()
