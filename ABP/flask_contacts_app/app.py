from flask import Flask, render_template, request, session, redirect, url_for
import joblib
import os
from modelo_decision import Stack, Queue
from werkzeug.security import generate_password_hash, check_password_hash
from keras.models import load_model  # Keras standalone
import numpy as np
from sentence_transformers import SentenceTransformer
import subprocess
import json
import requests
import re
import csv
from datetime import datetime

# Historial de conversación por usuario
historial_conversaciones = {}

def obtener_respuesta_ollama(mensaje):
    try:
        resultado = subprocess.run(
            ["ollama", "run", "llama3", mensaje],
            capture_output=True,
            text=False,  # Importante: recibir bytes
            timeout=30
        )
        texto = resultado.stdout.decode('utf-8').strip()  # Forzar UTF-8
        texto = re.sub(r'\x1b\[[0-9;]*m', '', texto)  # Limpiar colores ANSI
        return texto
    except Exception as e:
        return f"return Lo siento, no pude procesar tu mensaje en este momento. ¿Podrías intentarlo de nuevo? {str(e)}"

def guardar_en_historial(entrada_usuario, respuesta):
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("historial_chat.txt", "a", encoding="utf-8") as f:
        f.write(f"[{fecha_hora}]\nUsuario: {entrada_usuario}\nMOGI: {respuesta}\n\n")


def fusionar_respuestas_generadas(original="respuestas_IA.csv", generadas="respuestas_generadas.csv"):
    import pandas as pd
    import os

    if not os.path.exists(original):
        return False, "No se encontró el archivo original."

    if not os.path.exists(generadas):
        return False, "No hay nuevas respuestas generadas."

    try:
        df_original = pd.read_csv(original)
        df_generadas = pd.read_csv(generadas, names=["frase", "respuesta"])

        if 'frase' not in df_original.columns or 'respuesta' not in df_original.columns:
            return False, "El archivo original no tiene columnas correctas."

        frases_existentes = set(df_original['frase'].astype(str).str.lower())
        nuevas_filas = df_generadas[~df_generadas['frase'].astype(str).str.lower().isin(frases_existentes)]

        if not nuevas_filas.empty:
            df_actualizado = pd.concat([df_original, nuevas_filas], ignore_index=True)
            df_actualizado.to_csv(original, index=False)
            mensaje = f"Se agregaron {len(nuevas_filas)} nuevas frases."
        else:
            mensaje = "No hay frases nuevas para agregar."

        procesado_path = generadas.replace(".csv", "_procesadas.csv")
        os.rename(generadas, procesado_path)

        return True, mensaje + f" Respuestas fusionadas correctamente."
    except Exception as e:
        return False, f"Ocurrió un error al fusionar: {e}"



##########################################################################################
# Cargar modelo neuronal y modelo de embeddings
modelo_chatbot = load_model("flask_contacts_app/modelo_chatbot.keras")
modelo_bert = SentenceTransformer("all-MiniLM-L6-v2")

# Frases y respuestas del chatbot 
import pandas as pd
data_chatbot = pd.read_csv("respuestas_IA.csv", encoding="utf-8")
frases = data_chatbot["frase"].tolist()
respuestas = data_chatbot["respuesta"].tolist()

# Vectorizar todas las frases
frases_vectorizadas = modelo_bert.encode(frases)
########################################################################################


# Clase Diario
class Diario:
    def __init__(self):
        self.entradas = {}
    def agregar_entrada(self, fecha, estado_emocional, emocion, evento_inusual):
        self.entradas[fecha] = {
            "estado_emocional": estado_emocional,
            "emocion": emocion,
            "evento_inusual": evento_inusual
        }
    def listar_entradas(self):
        return self.entradas

# Clase Usuario
class Usuario:
    usuarios = []

    def __init__(self, nombre, email, contraseña, rol="usuario"):
        self.nombre = nombre
        self.email = email
        self.contraseña_hash = generate_password_hash(contraseña)
        self.rol = rol
        self.diario = Diario()

    def verificar_contraseña(self, contraseña):
        return check_password_hash(self.contraseña_hash, contraseña)

    @classmethod
    def verificar_login(cls, nombre, contraseña):
        for usuario in cls.usuarios:
            if usuario.nombre == nombre and usuario.verificar_contraseña(contraseña):
                return usuario
        return None

    @classmethod
    def eliminar_usuario(cls, nombre_usuario):
        cls.usuarios = [usuario for usuario in cls.usuarios if usuario.nombre != nombre_usuario]

    @classmethod
    def obtener_usuarios(cls):
        return cls.usuarios

# Clase Administrador
class Administrador(Usuario):
    def __init__(self, nombre, email, contraseña):
        super().__init__(nombre, email, contraseña, rol="admin")

# Crear usuarios
usuario1 = Usuario("Pedro", "pedro@unilasallista.edu.co", "1500")
usuario2 = Usuario("Miguel", "miguel@unilasallista.edu.co", "3000")
usuario3 = Administrador("Ast", "AsterStar@unilasallista.edu.co", "9191")
usuario4 = Administrador("Miguelord", "Miguelord@unilasallista.edu.co", "1515")
Usuario.usuarios.extend([usuario1, usuario2, usuario3, usuario4])

# Inicializar Flask
app = Flask(__name__)
diario = Diario()
app.secret_key = "tu_clave_secreta_segura"

# Rutas Flask
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = request.form["nombre"]
        contraseña = request.form["contraseña"]
        usuario = Usuario.verificar_login(nombre, contraseña)
        if usuario:
            session["usuario"] = {"nombre": usuario.nombre, "rol": usuario.rol}
            return render_template('index.html', usuario=usuario.nombre, rol=usuario.rol)
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")
    return render_template('login.html')

@app.route("/index", methods=["GET", "POST"])
def index():
    usuario_sesion = session.get("usuario")
    if usuario_sesion:
        return render_template("index.html", usuario=usuario_sesion["nombre"], rol=usuario_sesion["rol"])
    else:
        return render_template("login.html", error="Por favor inicia sesión")
    
@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")
    
    nombre = usuario_sesion["nombre"]
    rol = usuario_sesion["rol"]

    if request.method == "POST":
        data = request.get_json()
        mensaje_usuario = data.get("mensaje", "").strip()

        if not mensaje_usuario:
            return {"respuesta": "Por favor, escribe algo."}

        try:
            vector_usuario = modelo_bert.encode([mensaje_usuario])
            similitudes = np.dot(frases_vectorizadas, vector_usuario.T).flatten()
            indice_mas_similar = np.argmax(similitudes)

            if similitudes[indice_mas_similar] < 0.75:
                respuesta = obtener_respuesta_ollama(mensaje_usuario)
            else:
                respuesta = respuestas[indice_mas_similar]

            guardar_en_historial(mensaje_usuario, respuesta)
            return {"respuesta": respuesta}

        except Exception as e:
            return {"respuesta": f"Ocurrió un error al procesar tu mensaje: {str(e)}"}

    return render_template("chatbot.html", usuario=nombre, rol=rol)

@app.route("/historial")
def historial_view():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")
    
    nombre = usuario_sesion["nombre"]
    
    # Cargar historial desde archivo
    historial = []
    if os.path.exists("historial_chat.txt"):
        with open("historial_chat.txt", "r", encoding="utf-8") as f:
            bloques = f.read().split("\n\n")
            for bloque in bloques:
                partes = bloque.strip().split("\n")
                if len(partes) >= 3:
                    usuario_line = partes[1].replace("Usuario: ", "")
                    mogi_line = partes[2].replace("MOGI: ", "")
                    historial.append({"mensaje": usuario_line, "respuesta": mogi_line})
    
    return render_template("historial.html", historial=historial, usuario=nombre, rol=usuario_sesion["rol"])


@app.route("/diario", methods=["GET", "POST"])
def diario_view():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")
    nombre = usuario_sesion["nombre"]
    rol = usuario_sesion["rol"]

    if request.method == "POST":
        fecha = request.form["fecha"]
        sentimientos = request.form["sentimientos"]
        emociones = request.form.getlist("emociones")
        anomalias = request.form.get("anomalias", "")
        nueva_entrada = {
            "fecha": fecha,
            "estado_emocional": sentimientos,
            "emocion": emociones,
            "evento_inusual": anomalias
        }
        print(nueva_entrada)
        return render_template("diario.html", mensaje="Entrada guardada con éxito", entradas={fecha: nueva_entrada}, usuario=nombre, rol=rol)

    return render_template("diario.html", entradas={}, usuario=nombre, rol=rol)

@app.route('/galeria', methods=["GET", "POST"])
def galeria():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")    
    nombre = usuario_sesion["nombre"]
    rol = usuario_sesion["rol"]
    return render_template('galeria.html', usuario=nombre, rol=rol)

@app.route('/depre', methods=["GET", "POST"])
def depresion():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")
    return render_template('depresion.html', usuario=usuario_sesion["nombre"], rol=usuario_sesion["rol"])

@app.route('/ansiedad', methods=["GET", "POST"])
def ansiedad():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")
    return render_template('ansiedad.html', usuario=usuario_sesion["nombre"], rol=usuario_sesion["rol"])

@app.route('/insomnio', methods=["GET", "POST"])
def insomnio():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")    
    nombre = usuario_sesion["nombre"]
    rol = usuario_sesion["rol"]
    return render_template('insomnio.html', usuario=nombre, rol=rol)

@app.route('/anorexia', methods=["GET", "POST"])
def anorexia():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")    
    nombre = usuario_sesion["nombre"]
    rol = usuario_sesion["rol"]
    return render_template('anorexia.html', usuario=nombre, rol=rol)

@app.route('/sesiones', methods=["GET", "POST"])
def sesiones():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")
    return render_template('sesiones.html', usuario=usuario_sesion["nombre"], rol=usuario_sesion["rol"])

@app.route('/evaluacioniniciales', methods=["GET", "POST"])
def evaluacionesiniciales():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")
    return render_template('evaluacionesiniciales.html', usuario=usuario_sesion["nombre"], rol=usuario_sesion["rol"])

@app.route("/configuracion", methods=["GET", "POST"])
def configuracion():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")

    usuarios = Usuario.obtener_usuarios()
    if request.method == "POST":
        nombre_usuario_a_eliminar = request.form.get("eliminar_usuario")
        if nombre_usuario_a_eliminar:
            Usuario.eliminar_usuario(nombre_usuario_a_eliminar)
            return redirect(url_for('configuracion'))
        else:
            return render_template("configuracion.html", usuarios=usuarios, error="No se proporcionó un nombre válido")
    return render_template("configuracion.html", usuarios=usuarios)

# Cargar el modelo de árbol de decisión
modelo_path = os.path.join(os.path.dirname(__file__), "modelo_decision.pkl")
modelo, estados = joblib.load(modelo_path)

@app.route("/ejercicios", methods=["GET", "POST"])
def ejercicios():
    usuario_sesion = session.get("usuario")
    if not usuario_sesion:
        return render_template("login.html", error="Por favor inicia sesión")

    nombre = usuario_sesion["nombre"]
    rol = usuario_sesion["rol"]
    estado_predicho = None
    logs = []

    if request.method == "POST":
        try:
            task_queue = Queue()
            task_stack = Stack()
            logs = []

            task_queue.enqueue("Cargar datos")
            task_queue.enqueue("Entrenar modelo")
            task_queue.enqueue("Guardar modelo")
            logs.extend(task_queue.get_logs())

            current_task = task_queue.dequeue()
            logs.extend(task_queue.get_logs())
            task_stack.push(current_task)
            logs.extend(task_stack.get_logs())

            nivel_estres = float(request.form["nivel_estres"])
            horas_sueno = float(request.form["horas_sueno"])
            actividad_fisica = float(request.form["actividad_fisica"])

            prediccion = modelo.predict([[nivel_estres, horas_sueno, actividad_fisica]])
            estado_predicho = estados[prediccion[0]]

            task_stack.pop()
            logs.extend(task_stack.get_logs())

        except Exception as e:
            logs.append(f"Error: {str(e)}")

    return render_template('arbol.html', usuario=nombre, rol=rol, estado=estado_predicho, logs=logs)

if __name__ == "__main__":
    contraseña_prueba = "1234"

    hash_generado = generate_password_hash(contraseña_prueba)
    print("Contraseña original:", contraseña_prueba)
    print("Hash generado:", hash_generado)

    es_valido = check_password_hash(hash_generado, contraseña_prueba)
    print("¿Verificacion exitosa?:", es_valido)
    app.run(debug=True)

@app.route("/chat", methods=["POST"])
def chat():
    entrada = request.form["mensaje"]
    respuesta = chatbot.responder(entrada)

