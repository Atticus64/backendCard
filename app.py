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
    def __init__(self, id, nombre, autor, reseña, portada_url, isbn, anio):
        self.id = id
        self.nombre = nombre
        self.autor = autor
        self.reseña = reseña
        self.portada_url = portada_url
        self.isbn = isbn
        self.year = anio

    
    @classmethod
    def from_row(cls, row):
      return cls(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

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

# GET requests will be blocked
@app.route('/get_type_read', methods=['POST'])
def get_type():
    request_data = request.get_json()

    id = request_data['id']

    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_usuario
        FROM usuario
        WHERE id_nfc = %s
    """, (id,))

    data = cursor.fetchone()

    if data is not None:
        conn.close()
        return  {
            "ok": True,
            "type": "user",
        }
    
    cursor.execute("""
        SELECT id_libro
        FROM ejemplar
        WHERE id_nfc = %s
        """, (id,))
    data = cursor.fetchone()
    conn.close()

    if data is not None:
        return {
            "ok": True,
            "type": "book",
        }

    return {
        "ok": False,
        "msg": "NFC ID not found"
    }

@app.route("/prestamo", methods=['POST'])
def create_prestamo():
    # recibe el body el id_nfc del usuario y el id_nfc del ejemplar
    request_data = request.get_json()
    id_nfc_usuario = request_data.get("id_nfc_usuario")
    id_nfc_ejemplar = request_data.get("id_nfc_ejemplar")
    print(f"Creating prestamo for user {id_nfc_usuario} and ejemplar {id_nfc_ejemplar}")
    if not all([id_nfc_usuario, id_nfc_ejemplar]):
        fields = []
        if id_nfc_usuario is None:
            fields.append("id_nfc_usuario")
        if id_nfc_ejemplar is None:
            fields.append("id_nfc_ejemplar")
             
        return {
            "ok": False,
            "msg": "Missing required fields",
            "fields": fields
        }
    conn = get_db_conn()
    cursor = conn.cursor()
    # validar que el id_nfc del usuario exista
    cursor.execute("SELECT id_usuario FROM usuario WHERE id_nfc = %s", (id_nfc_usuario,))
    user = cursor.fetchone()
    if user is None:
        return {
            "ok": False,
            "msg": "User not found"
        }
    # validar que el id_nfc del ejemplar exista
    cursor.execute("SELECT id_ejemplar FROM ejemplar WHERE id_nfc = %s", (id_nfc_ejemplar,))
    ejemplar = cursor.fetchone()
    if ejemplar is None:
        return {
            "ok": False,
            "msg": "Ejemplar not found"
        }

    # ejemplo de query para insertar un prestamo
    #INSERT INTO prestamo (
    #    id_ejemplar,
    #    fecha_devolucion,
    #    id_usuario,
    #    fecha_prestamo,
    #    estatus
    #) VALUES (
    #    5000000001,                       -- id del ejemplar (debe existir en la tabla ejemplar)
    #    '2025-06-10 23:59:59',     -- fecha de devolución estimada
    #    4,                        -- id del usuario (debe existir en la tabla usuario)
    #    NOW(),                     -- fecha actual como fecha del préstamo
    #    'Activo'                   -- estatus actual del préstamo
    #);

    # verificar si el ejemplar ya está prestado
    cursor.execute("""
        SELECT id_prestamo FROM prestamo 
        WHERE id_ejemplar = %s AND estatus = 'Activo'
    """, (ejemplar[0],))

    prestamo = cursor.fetchone()
    if prestamo is not None:
        return {
            "ok": False,
            "msg": "Ejemplar is already borrowed"
        }

    try:
        # para verificar ejemplo, el prestamo dure un minuto 
        #        NOW() + INTERVAL '15 days',  -- 15 days from now
        # cursor.execute("""

        # marcar el ejemplar como prestado
        #     UPDATE ejemplar SET estatus = 'Prestado' WHERE id_ejemplar = %s
        cursor.execute("""
            UPDATE ejemplar SET disponibilidad = false
            WHERE id_ejemplar = %s
        """, (ejemplar[0],))
        
        
        cursor.execute("""
            INSERT INTO prestamo (
                id_ejemplar,
                fecha_devolucion,
                id_usuario,
                fecha_prestamo,
                estatus
            ) VALUES (
                %s, 
                NOW() + INTERVAL '1 minutes',
                %s, 
                NOW(), 
                'Activo'
            )
        """, (ejemplar[0], user[0]))

        conn.commit()

    except psycopg2.Error as e:
        conn.rollback()
        return {
            "ok": False,
            "msg": f"Error creating prestamo: {e}"
        }
    finally:
        cursor.close()
        conn.close()

    return {
        "ok": True,
        "msg": "Prestamo created successfully"
    }


@app.route("/prestamo/devolver", methods=['POST'])
def devolver_prestamo():
    conn = get_db_conn()
    cursor = conn.cursor()
    # recibe? el id_nfc del ejemplar
    
    request_data = request.get_json()
    id_nfc_ejemplar = request_data.get("id_nfc_ejemplar")
    if id_nfc_ejemplar is None:
        return {
            "ok": False,
            "msg": "Missing required fields",
            "fields": ["id_nfc_ejemplar"]
        }
        
    # validar que el id_nfc del ejemplar exista
    cursor.execute("SELECT id_ejemplar FROM ejemplar WHERE id_nfc = %s", (id_nfc_ejemplar,))
    ejemplar = cursor.fetchone()
    if ejemplar is None:
        return {
            "ok": False,
            "msg": "Ejemplar no encontrado"
        }
        
    # verificar si el ejemplar está prestado
    cursor.execute("""
        SELECT id_prestamo FROM prestamo
        WHERE id_ejemplar = %s AND estatus = 'Activo'
    """, (ejemplar[0],))
    prestamo = cursor.fetchone()
    if prestamo is None:
        return {
            "ok": False,
            "msg": "El ejemplar no está prestado o ya ha sido devuelto"
        }
    try:
        # actualizar el estatus del prestamo a 'Devuelto'
        cursor.execute("""
            UPDATE prestamo 
            SET estatus = 'Devuelto', fecha_devolucion = NOW()
            WHERE id_prestamo = %s
        """, (prestamo[0],))

        # marcar el ejemplar como disponible
        cursor.execute("""
            UPDATE ejemplar SET disponibilidad = true
            WHERE id_ejemplar = %s
        """, (ejemplar[0],))

        conn.commit()

    except psycopg2.Error as e:
        conn.rollback()
        return {
            "ok": False,
            "msg": f"Error regresando prestamo: {e}"
        }

    finally:
        cursor.close()
        conn.close()
    return {
        "ok": True,
        "msg": "Prestamo devuelto exitosamente"
    }

@app.route("/ejemplar/nfc/<string:id>")
def get_ejemplar_by_nfc(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_ejemplar, ejemplar.isbn, ejemplar.anio_publicacion, 
        book.nombre as titulo, portada_url, autor.nombre as autor
        FROM ejemplar 
        join book on ejemplar.id_libro = book.id
        join autor on book.id_autor = autor.id_autor
        WHERE ejemplar.id_nfc = %s
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

@app.route("/books/nfc/<string:id>")
def get_book_by_nfc(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT book.id, book.nombre as titulo, autor.nombre as autor,   
            book.reseña as reseña, portada_url, isbn, anio_publicacion
        FROM ejemplar 
        join book on ejemplar.id_libro = book.id
        join autor on book.id_autor = autor.id_autor
        WHERE ejemplar.id_nfc = %s
                   """, (id,))

    data = cursor.fetchone()

    if data is None:
        return {
            "ok": False,
            "msg": "Book not found"
        }

    book = Book.from_row(data)

    conn.close()

    return {
        "ok": True,
        "book": book.__dict__
    }
    

@app.route("/users/nfc/<string:id>")
def get_user_by_nfc(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_usuario as id, usuario.nombre, correo, carrera.nombre as carrera,
        tipo_usuario.nombre as tipo_usuario
        FROM usuario
        left join carrera on usuario.id_carrera = carrera.id_carrera
        join tipo_usuario on usuario.id_tipo_usuario = tipo_usuario.id
        WHERE id_nfc = %s
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
        "email": data[2],
        "carrera": data[3],
        "tipo_usuario": data[4]
    }

    conn.close()

    return {
        "ok": True,
        "user": user
    }

@app.route("/tipos_usuario")
def get_types_user():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre
        FROM tipo_usuario
    """)

    data = cursor.fetchall()

    if len(data) == 0:
        return {
            "ok": False,
            "msg": "No types found"
        }

    types = []
    for row in data:
        types.append({
            "id": row[0],
            "nombre": row[1]
        })

    conn.close()

    return {
        "ok": True,
        "types": types
    }

@app.route("/user/create", methods=['POST'])
def create_user():
    # debe de venir en el body
    # {
    #   "nombre": "Nombre del usuario",
    #   "email": "
    #   "telefono"
    #   "carrera": "ID de la carrera", puede ser null
    #   "tipo_usuario": "ID del tipo de usuario",
    #   "id_nfc": "ID del NFC"
    # }   
    #}
    request_data = request.get_json()
    nombre = request_data.get("nombre")
    email = request_data.get("correo")
    telefono = request_data.get("telefono")
    carrera = request_data.get("carrera")
    tipo_usuario = request_data.get("tipo_usuario")
    id_nfc = request_data.get("id_nfc")

    if not all([nombre, email, telefono, tipo_usuario, id_nfc]):

        return {
            "ok": False,
            "msg": "Missing required fields"
        }

    conn = get_db_conn()
    cursor = conn.cursor()

    # validar que otro usuario no tenga el mismo correo
    cursor.execute("SELECT id_usuario FROM usuario WHERE correo = %s", (email,))
    existing_user = cursor.fetchone()
    if existing_user is not None:
        return {
            "ok": False,
            "msg": "User with this email already exists"
        }
    # validar si el id_nfc existe y volverlo nulo en la otra cuenta
    cursor.execute("SELECT id_usuario FROM usuario WHERE id_nfc = %s", (id_nfc,))
    existing_nfc = cursor.fetchone()
    if existing_nfc is not None:
        cursor.execute("UPDATE usuario SET id_nfc = NULL WHERE id_nfc = %s", (id_nfc,))
        conn.commit()
        if cursor.rowcount == 0:
            return {
                "ok": False,
                "msg": "NFC ID not found in any user"
            }
    # validar que el tipo de usuario exista
    cursor.execute("SELECT id FROM tipo_usuario WHERE id = %s", (tipo_usuario,))
    existing_type = cursor.fetchone()
    if existing_type is None:
        return {
            "ok": False,
            "msg": "User type does not exist"
        }
    # validar que la carrera exista
    if carrera is not None:
        cursor.execute("SELECT id_carrera FROM carrera WHERE id_carrera = %s", (carrera,))
        existing_career = cursor.fetchone()
        if existing_career is None:
            return {
                "ok": False,
                "msg": "Career does not exist"
            }
    else:
        carrera = None
    try:
        # get last id_usuario
        cursor.execute("SELECT MAX(id_usuario) FROM usuario")
        last_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO usuario (id_usuario, nombre, correo, telefono, id_carrera, id_tipo_usuario, fecha_registro, id_nfc)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (last_id + 1, nombre, email, telefono, carrera, tipo_usuario, id_nfc))
        conn.commit()   
    except psycopg2.Error as e:
        conn.rollback()
        return {
            "ok": False,
            "msg": f"Error creating user: {e}"
        }
    finally:
        cursor.close()
        conn.close()   

    return {
        "ok": True,
        "msg": "User created successfully"
    }
    
    

@app.route("/carreras")
def get_carreras():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_carrera, nombre
        FROM carrera
    """)

    data = cursor.fetchall()

    if len(data) == 0:
        return {
            "ok": False,
            "msg": "No carreras found"
        }

    carreras = []
    for row in data:
        carreras.append({
            "id": row[0],
            "nombre": row[1]
        })

    conn.close()

    return {
        "ok": True,
        "carreras": carreras
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
        SELECT DISTINCT ON (book.id) book.id, book.nombre as titulo, autor.nombre as autor,   
            book.reseña as reseña, portada_url, isbn, anio_publicacion
        FROM book 
        join autor on book.id_autor = autor.id_autor
        join ejemplar on book.id = ejemplar.id_libro
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
