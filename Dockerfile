# Imagen base oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de dependencias y la app
COPY requirements.txt ./
COPY . .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto en el que corre Flask (por defecto 5000)
EXPOSE 8000

# Comando para ejecutar la app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

