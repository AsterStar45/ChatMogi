# --- Importaciones y definición de clases ---
import os
import pandas as pd
import numpy as np
import pickle
import requests
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer, util
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from datetime import datetime
import csv
import json
import ollama

def generar_respuesta_llama(mensaje_usuario, historial):
    try:
        contexto = "\n".join([f"Usuario: {u}\nMOGI: {b}" for u, b in historial])
        prompt = (
            "Estás hablando como un asistente empático llamado MOGI. "
            "Responde siempre en español y de forma humana, sin juicios. "
            "Solo responde preguntas que creas tengan que ver con la salud mental, o que ayuden a la salud mental del usuario. "
            "Bajo ninguna circunstancia hables inglés. "
            "La conversación hasta ahora es:\n\n"
            f"{contexto}\nUsuario: {mensaje_usuario}\nMOGI:"
        )

        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': 'llama3', 'prompt': prompt, 'stream': False},
            timeout=30
        )

        data = response.json()
        respuesta = data.get("response", "").strip()

        return respuesta if respuesta else "No se recibió respuesta de LLaMA."

    except Exception as e:
        print(f"[ERROR] No se pudo conectar con Ollama: {e}")
        return "Lo siento, no pude generar una respuesta en este momento."


class ChatBotRedNeuronal:

    def __init__(self, csv_path):
        self.historial_sesion = []  # Lista de tuplas (entrada_usuario, respuest
        self.csv_path = csv_path
        self.modelo_path = os.path.join(os.path.dirname(__file__), "modelo_chatbot.keras")
        self.label_encoder_path = os.path.join(os.path.dirname(__file__), "label_encoder.pkl")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        

        self.data = pd.read_csv(csv_path)
        if 'frase' not in self.data.columns or 'respuesta' not in self.data.columns:
            raise ValueError("El CSV debe contener las columnas 'frase' y 'respuesta'")

        self.frases = self.data['frase'].astype(str).tolist()
        self.respuestas = self.data['respuesta'].astype(str).tolist()

        self.label_encoder = LabelEncoder()
        self.labels = self.label_encoder.fit_transform(self.respuestas)
        self.num_clases = len(set(self.labels))

        with open(self.label_encoder_path, "wb") as f:
            pickle.dump(self.label_encoder, f)

        self.embeddings = self.embedding_model.encode(self.frases, convert_to_numpy=True)

        if os.path.exists(self.modelo_path):
            self.modelo = load_model(self.modelo_path)
        else:
            self.entrenar_modelo()

        

    def entrenar_modelo(self):
        X_train, X_test, y_train, y_test = train_test_split(
            self.embeddings, self.labels, test_size=0.2, random_state=42
        )

        model = Sequential()
        model.add(Dense(128, activation='relu', input_shape=(X_train.shape[1],)))
        model.add(Dropout(0.3))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(self.num_clases, activation='softmax'))

        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

        early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

        model.fit(X_train, y_train, epochs=50, batch_size=16, validation_data=(X_test, y_test), callbacks=[early_stop])

        model.save(self.modelo_path)
        self.modelo = model

    def obtener_respuesta(self, entrada_usuario):
        embedding_usuario = self.embedding_model.encode([entrada_usuario])[0]
        similitudes = util.cos_sim(embedding_usuario, self.embeddings)[0]
        indice_mejor = np.argmax(similitudes)
        mejor_sim = similitudes[indice_mejor]

        if mejor_sim >= 0.85:
            respuesta = self.respuestas[indice_mejor]
        else:
            respuesta = generar_respuesta_llama(entrada_usuario, self.historial_sesion)
            with open("respuestas_generadas.csv", "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([entrada_usuario, respuesta])
        
        self.historial_sesion.append((entrada_usuario, respuesta))  # Guarda la conversación reciente

        # Guardar historial en archivo de texto
        
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("historial_chat.txt", "a", encoding="utf-8") as f_hist:
            f_hist.write(f"[{fecha_hora}]\nUsuario: {entrada_usuario}\nMOGI: {respuesta}\n\n")


        return respuesta


#Registra, exporta y hace todo lo relacionado al historial
    @staticmethod
    def registrar_conversacion(entrada, salida):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("historial_chat.txt", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}]\nUsuario: {entrada}\nMOGI: {salida}\n\n")
        except Exception as e:
            print(f"[ERROR] No se pudo guardar la conversación: {e}")

    def mostrar_historial(self):
        try:
            with open("historial_chat.txt", "r", encoding="utf-8") as f:
                print(f.read())
        except FileNotFoundError:
            print("Aún no hay historial guardado.")

    def exportar_historial_csv(self, output_csv="historial_chat.csv"):
        try:
            if not os.path.exists("historial_chat.txt"):
                print("No hay historial para exportar.")
                return

            with open("historial_chat.txt", "r", encoding="utf-8") as txt_file:
                lineas = txt_file.readlines()

            registros = []
            for i in range(0, len(lineas), 4):
                if i + 2 < len(lineas):
                    timestamp = lineas[i].strip().replace("[", "").replace("]", "")
                    entrada = lineas[i + 1].replace("Usuario: ", "").strip()
                    respuesta = lineas[i + 2].replace("MOGI: ", "").strip()
                    registros.append([timestamp, entrada, respuesta])

            with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Fecha y Hora", "Entrada Usuario", "Respuesta MOGI"])
                writer.writerows(registros)

            print(f"Historial exportado correctamente a {output_csv}")

        except Exception as e:
            print(f"[ERROR] No se pudo exportar el historial: {e}")

#Función que agrega las respuestas generadas por LLaMA al dataset para que se reentrebe al fusionar respuestas

def fusionar_respuestas_generadas(original="respuestas_IA.csv", generadas="respuestas_generadas.csv"):
    import pandas as pd
    import os

    if not os.path.exists(original):
        print(f"[ERROR] No se encontró el archivo original: {original}")
        return
    if not os.path.exists(generadas):
        print(f"[INFO] No hay nuevas respuestas generadas aún ({generadas} no existe).")
        return

    try:
        df_original = pd.read_csv(original)
        df_generadas = pd.read_csv(generadas, names=["frase", "respuesta"])

        if 'frase' not in df_original.columns or 'respuesta' not in df_original.columns:
            print("[ERROR] El archivo original debe tener las columnas 'frase' y 'respuesta'")
            return

        frases_existentes = set(df_original['frase'].astype(str).str.lower())
        nuevas_filas = df_generadas[~df_generadas['frase'].astype(str).str.lower().isin(frases_existentes)]

        if not nuevas_filas.empty:
            df_actualizado = pd.concat([df_original, nuevas_filas], ignore_index=True)
            df_actualizado.to_csv(original, index=False)
            print(f"[✔] Se agregaron {len(nuevas_filas)} nuevas frases a {original}.")
        else:
            print("[ℹ] No hay frases nuevas para agregar. Todo está actualizado.")

        # Renombrar el archivo de generadas
        procesado_path = generadas.replace(".csv", "_procesadas.csv")
        os.rename(generadas, procesado_path)
        print(f"[✔] El archivo '{generadas}' fue renombrado como '{procesado_path}'.")

    except Exception as e:
        print(f"[ERROR] Falló la fusión de respuestas: {e}")




# --- Bloque principal (fuera de la clase) ---
if __name__ == "__main__":
    chatbot = ChatBotRedNeuronal("respuestas_IA.csv")
    print(" MOGI está listo para ayudarte. Escribe 'salir' para terminar.\n")

    while True:
        entrada = input("Tú: ")
        if entrada.lower() in ["salir", "exit", "quit"]:
            print("MOGI: ¡Hasta luego! 💬") 
            break
        elif entrada.lower() == "ver historial":
            chatbot.mostrar_historial()
        elif entrada.lower() in ["exportar historial", "exportar csv"]:
            chatbot.exportar_historial_csv()
        elif entrada.lower() in ["fusionar respuestas", "actualizar base"]:
            fusionar_respuestas_generadas(original=chatbot.csv_path)
            print("[🔁] Entrenando el modelo con las nuevas respuestas...")
            chatbot = ChatBotRedNeuronal(chatbot.csv_path)  # Reinicializa y reentrena
            print("[✔] Modelo actualizado con nuevas respuestas.")
        else:
            respuesta = chatbot.obtener_respuesta(entrada)
            print("")