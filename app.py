import psycopg2
from dotenv import load_dotenv
from flask import Flask
import os

load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

app = Flask(__name__)

def get_db_conn():
    conn = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )

    return conn

@app.route("/")
def hello_world():
    return "<p>Hola api development!</p>"

@app.route("/health")
def health():
    return {
        "ok": True,
        "msg": "All file dude!"
    }

@app.route("/books")
def get_books():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM book order by id")
    books = cursor.fetchall()
    conn.close()
    return {
        "ok": True,
        "books": books
    }
