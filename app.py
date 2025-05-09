import psycopg2
from dotenv import load_dotenv
from flask import Flask
import os
from flask_cors import CORS

load_dotenv()

DB_URL = os.getenv("database_url")
app = Flask(__name__)
CORS(app)

def get_db_conn():
    conn = psycopg2.connect(
        DB_URL
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

    def get(self):
        return repo.get_all(), 200, {'Access-Control-Allow-Origin': '*'}
    return {
        "ok": True,
        "books": books
    }
