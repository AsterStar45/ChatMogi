import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier, plot_tree
import os
from collections import deque

# Definir clases para Pila y Cola
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)
        print(f'Elemento "{item}" añadido a la pila.')

    def pop(self):
        if not self.is_empty():
            removed_item = self.items.pop()
            print(f'Elemento "{removed_item}" removido de la pila.')
            return removed_item
        else:
            print('La pila está vacía, no se puede realizar la operación pop.')

    def is_empty(self):
        return len(self.items) == 0

    def display(self):
        print(f'Estado actual de la pila: {self.items}')

class Queue:
    def __init__(self):
        self.queue = deque()

    def enqueue(self, item):
        self.queue.append(item)
        print(f"Tarea '{item}' añadida a la cola.")

    def dequeue(self):
        if not self.is_empty():
            item = self.queue.popleft()
            print(f"Tarea '{item}' removida de la cola.")
            return item
        else:
            print("La cola está vacía.")
            return None

    def display(self):
        print("Queue contents:", list(self.queue))

    def is_empty(self):
        return len(self.queue) == 0

# Crear estructuras de datos para tareas
task_queue = Queue()
task_stack = Stack()

# Agregar tareas iniciales a la cola
task_queue.enqueue("Cargar datos")
task_queue.enqueue("Entrenar modelo")
task_queue.enqueue("Guardar modelo")

# Ruta del archivo CSV
ruta_csv = os.path.join(os.path.dirname(__file__), "datos_salud_mental.csv")

if not os.path.exists(ruta_csv):
    print(f"Error: No se encontró el archivo en {ruta_csv}")
    exit()

# Mover la tarea a la pila y ejecutar
current_task = task_queue.dequeue()
task_stack.push(current_task)

data = pd.read_csv(ruta_csv)
print("Datos cargados correctamente")
task_stack.pop()

# Codificar la variable categórica 'estado'
task_stack.push("Codificar datos")
le = LabelEncoder()
data["estado_num"] = le.fit_transform(data["estado"])
task_stack.pop()

# Definir variables predictoras y objetivo
task_stack.push("Dividir datos")
X = data[["nivel_estres", "horas_sueno", "actividad_fisica"]]
y = data["estado_num"]
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
task_stack.pop()

# Entrenar el modelo
task_stack.push("Entrenar modelo")
modelo = DecisionTreeClassifier()
modelo.fit(x_train, y_train)
task_stack.pop()

# Guardar el modelo
task_stack.push("Guardar modelo")
filename = os.path.join(os.path.dirname(__file__), "modelo_decision.pkl")
joblib.dump((modelo, le.classes_), filename)
print(f"Modelo guardado en {filename}")
task_stack.pop()

# Cargar el modelo
modelo, estados = joblib.load(filename)
print("Modelo cargado correctamente")

# Predicción con entrada del usuario
try:
    #nivel_estres = float(input("Ingrese el nivel de estrés (ejemplo: 2.5, 4, 6.7): "))
    #horas_sueno = float(input("Ingrese las horas de sueño: "))
    #actividad_fisica = float(input("Ingrese la cantidad de actividad física (en horas): "))

    #prediccion = modelo.predict([[nivel_estres, horas_sueno, actividad_fisica]])
    #print("Estado predicho:", le.inverse_transform(prediccion)[0])
    pass
except ValueError:
    #print("Error: Ingrese valores numéricos válidos.")
    pass