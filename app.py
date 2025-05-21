import psycopg2
from dotenv import load_dotenv
from flask import Flask
import os
from flask_cors import CORS

load_dotenv()

DB_URL = os.getenv("database_url")
app = Flask(__name__)
CORS(app)


class Book:
    def __init__(self, id, nombre, autor, reseña):
        self.id = id
        self.nombre = nombre
        self.autor = autor
        self.reseña = reseña

    
    @classmethod
    def from_row(cls, row):
      return cls(row[0], row[1], row[2], row[3])

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
    id = 2
    cursor.execute("""
        SELECT book.id, book.nombre as titulo, autor.nombre as autor,   
            book.reseña as reseña
        FROM book 
        join autor on book.id_autor = autor.id_autor
        WHERE book.id_autor = %s
                   """, (id,))

    data = cursor.fetchall()
    books = []

    for row in data:
        book = Book.from_row(row)
        books.append(book.__dict__)

    conn.close()

    return {
        "ok": True,
        "books": books
    }
