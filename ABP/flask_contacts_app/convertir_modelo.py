from tensorflow.keras.models import load_model

# Cargar el modelo en formato HDF5 (.h5)
modelo_h5 = load_model("modelo_chatbot.h5")

# Guardarlo en el nuevo formato Keras (.keras)
modelo_h5.save("modelo_chatbot.keras")

print("✅ Modelo convertido y guardado como modelo_chatbot.keras")
