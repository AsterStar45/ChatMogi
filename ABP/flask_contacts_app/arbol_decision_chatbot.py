import pandas as pd
import joblib
import os
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import make_pipeline
from fuzzywuzzy import fuzz
import unicodedata
import unicodedata

class ChatBotDecisionTree:

    def normalizar(texto):
        texto = texto.lower().strip()
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        return texto
    
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.modelo_path = os.path.join(os.path.dirname(__file__), "modelo_chatbot.pkl")
        self.data = pd.read_csv(csv_path)
        self.data['frase'] = self.data['frase'].apply(lambda x: self.quitar_tildes(str(x).lower()))


        # Validar columnas del CSV
        if 'frase' not in self.data.columns or 'respuesta' not in self.data.columns:
            raise ValueError("El CSV debe contener las columnas 'frase' y 'respuesta'")

        # Cargar modelo si existe, si no entrenar
        if os.path.exists(self.modelo_path):
            self.pipeline = joblib.load(self.modelo_path)
        else:
            self.entrenar_modelo()

    def entrenar_modelo(self):
        X_text = self.data['frase']
        y = self.data['respuesta']
        self.vectorizer = CountVectorizer()
        self.modelo = MultinomialNB()
        self.pipeline = make_pipeline(self.vectorizer, self.modelo)
        self.pipeline.fit(X_text, y)

        # Guardar el modelo entrenado
        joblib.dump(self.pipeline, self.modelo_path)
    
    def obtener_respuesta(self, frase):
        # Paso 1: Normaliza frase del usuario
        frase = frase.lower().strip()

        # Paso 2: Coincidencia exacta
        for _, row in self.data.iterrows():
            if frase == row['frase'].lower().strip():
                respuesta = row['respuesta']
                self.registrar_conversacion(frase, respuesta)
                return respuesta

        # Paso 3: Coincidencia difusa (fuzzy)
        mejor_score = 0
        mejor_respuesta = None
        for _, row in self.data.iterrows():
            score = fuzz.token_sort_ratio(frase, row['frase'])
            if score > mejor_score:
                mejor_score = score
                mejor_respuesta = row['respuesta']
    
        if mejor_score >= 85:  # Umbral de confianza
            self.registrar_conversacion(frase, mejor_respuesta)
            return mejor_respuesta

        # Paso 4: Predicción con el modelo entrenado (si nada coincidió antes)
        try:
            entrada_vectorizada = self.vectorizer.transform([frase])
            prediccion = self.modelo.predict(entrada_vectorizada)[0]
            respuesta = self.data.loc[prediccion, 'respuesta']
        except:
            respuesta = "Lo siento, no entendí eso. ¿Puedes reformularlo?"

        self.registrar_conversacion(frase, respuesta)
        return respuesta

    
    @staticmethod
    def quitar_tildes(texto):
        return ''.join((c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn'))

    @staticmethod
    def registrar_conversacion(entrada, salida):
        try:
            with open("historial_chat.txt", "a", encoding="utf-8") as f:
                f.write(f"Usuario: {entrada}\nMOGI: {salida}\n\n")
        except Exception as e:
            print(f"[ERROR] No se pudo guardar la conversación: {e}")

# Inicializar el chatbot con el árbol de decisión
csv_path = os.path.join(os.path.dirname(__file__), "respuestas_chatbot.csv")
chatbot = ChatBotDecisionTree(csv_path)

# Ejemplo de prueba
if __name__ == "__main__":
    print("Escribe 'salir' para terminar el chat.")
    while True:
        user_input = input("Tú: ")
        if user_input.lower() == "salir":
            break
        print("MOGI:", chatbot.obtener_respuesta(user_input))
