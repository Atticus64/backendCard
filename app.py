import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, jsonify
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

@app.route("/yomero")
def yomero():
    return "<p>Hello world!</p>"

@app.route("/health")
def health():
    return {
        "ok": True,
        "msg": "All file dude!"
    }

@app.route("/users/<string:id>")
def get_user(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_usuario as id, nombre, correo
        FROM usuario
        WHERE id_usuario = %s
                   """, (id,))

    data = cursor.fetchone()

    if data is None:
        return {
            "ok": False,
            "msg": "User not found"
        }

    user = {
        "id": data[0],
        "nombre": data[1],
        "email": data[2]
    }

    conn.close()

    return {
        "ok": True,
        "user": user
    }

@app.route("/users/nfc/<string:id>")
def get_user_by_nfc(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_usuario as id, nombre, correo
        FROM usuario
        WHERE nfc_id = %s
                   """, (id,))

    data = cursor.fetchone()

    if data is None:
        return {
            "ok": False,
            "msg": "User not found"
        }

    user = {
        "id": data[0],
        "nombre": data[1],
        "email": data[2]
    }

    conn.close()

    return {
        "ok": True,
        "user": user
    }

@app.route("/books/autor")
def get_books_by_autor():
    # get the query parameter
    query_uri = request.args.get("query")
    if query_uri is None or query_uri == "":
        return {
            "ok": False,
            "msg": "No query parameter provided"
        }

    conn = get_db_conn()
    cursor = conn.cursor()
    query = "%" + query_uri + "%"
    cursor.execute("""
        SELECT book.id, book.nombre as titulo, autor.nombre as autor,   
            book.reseña as reseña
        FROM book 
        join autor on book.id_autor = autor.id_autor
        WHERE autor.nombre like %s
        order by book.id 
                   """, (query,))
    data = cursor.fetchall()
    books = []
    for row in data:
        book = Book.from_row(row)
        books.append(book.__dict__)
    conn.close()
    if len(books) == 0:
        return {
            "ok": False,
            "msg": "No books found"
        }

    return {
        "ok": True,
        "books": books
    }

    

@app.route("/books")
def get_books():
    conn = get_db_conn()
    cursor = conn.cursor()
    #id = 2
    #cursor.execute("""
    #    SELECT book.id, book.nombre as titulo, autor.nombre as autor,   
    #        book.reseña as reseña
    #    FROM book 
    #    join autor on book.id_autor = autor.id_autor
    #    WHERE book.id_autor = %s
    #               """, (id,))
    cursor.execute("""
        SELECT book.id, book.nombre as titulo, autor.nombre as autor,   
            book.reseña as reseña
        FROM book 
        join autor on book.id_autor = autor.id_autor
        order by book.id
    """)

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

@app.route("/ejemplar/<id>")
def get_ejemplar(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_ejemplar, ejemplar.isbn, ejemplar.anio_publicacion, 
        book.nombre as titulo, portada_url, autor.nombre as autor
        FROM ejemplar 
        join book on ejemplar.id_libro = book.id
        join autor on book.id_autor = autor.id_autor
        WHERE id_ejemplar = %s
    """, (id,))
    data = cursor.fetchone()

    if data is None:
        return {
            "ok": False,
            "msg": "Ejemplar not found"
        }

    ejemplar = {
        "id": data[0],
        "isbn": data[1],
        "año_publicacion": data[2],
        "titulo": data[3],
        "portada_url": data[4],
        "autor": data[5]
    }

    conn.close()

    return {
        "ok": True,
        "ejemplar": ejemplar
    }
