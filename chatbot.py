import streamlit as st
import os
import csv
from datetime import datetime
import random

try:
    import openai
    openai_available = True
except ImportError:
    st.error("Error: La librería 'openai' no está instalada. Algunas funcionalidades no estarán disponibles.")
    openai_available = False

# Inicialización del cliente OpenAI solo si está disponible
if openai_available:
    openai.api_key = st.secrets.get("OPENAI_API_KEY", "")

# Inicialización de variables de estado de Streamlit
if 'menu' not in st.session_state:
    st.session_state.menu = {}
if 'delivery_cities' not in st.session_state:
    st.session_state.delivery_cities = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_order' not in st.session_state:
    st.session_state.current_order = []
if 'order_in_progress' not in st.session_state:
    st.session_state.order_in_progress = False

def load_menu_from_csv():
    try:
        with open('menu.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = row['Category']
                if category not in st.session_state.menu:
                    st.session_state.menu[category] = []
                st.session_state.menu[category].append(row)
    except FileNotFoundError:
        st.error("Error: El archivo 'menu.csv' no fue encontrado.")
    except KeyError as e:
        st.error(f"Error: La clave {e} no existe en el archivo 'menu.csv'. Verifica que los encabezados coincidan.")

def load_delivery_cities():
    try:
        with open('us-cities.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            st.session_state.delivery_cities = [f"{row['City']}, {row['State short']}" for row in reader]
    except FileNotFoundError:
        st.error("Error: El archivo 'us-cities.csv' no fue encontrado.")

def initialize_chatbot():
    load_menu_from_csv()
    load_delivery_cities()
    st.success("¡Chatbot inicializado exitosamente!")

def moderate_content(message):
    offensive_words = ['palabrota1', 'palabrota2', 'palabrota3']  # Agrega más si es necesario
    return not any(word in message.lower() for word in offensive_words)

def process_user_query(query):
    if "menú" in query.lower() or "carta" in query.lower():
        return consult_menu_csv(query)
    elif "pedir" in query.lower() or "ordenar" in query.lower():
        return start_order_process(query)
    elif "cancelar" in query.lower() or "anular" in query.lower():
        return cancel_order()
    elif "confirmar" in query.lower():
        return confirm_order()
    elif "entrega" in query.lower() or "reparto" in query.lower():
        return consult_delivery_cities(query)
    elif "información nutricional" in query.lower() or "calorías" in query.lower():
        return get_nutritional_info(query)
    else:
        return process_general_query(query)

def consult_menu_csv(query):
    response = "Aquí está nuestro menú:\n\n"
    for category, items in st.session_state.menu.items():
        response += f"{category}:\n"
        for item in items:
            response += f"- {item['Item']}: {item['Serving Size']}, {item['Calories']} calorías\n"
        response += "\n"
    return response

def get_nutritional_info(query):
    item_name = query.split("de")[-1].strip().lower()
    for category, items in st.session_state.menu.items():
        for item in items:
            if item['Item'].lower() == item_name:
                return f"Información nutricional para {item['Item']}:\n" \
                       f"Tamaño de porción: {item['Serving Size']}\n" \
                       f"Calorías: {item['Calories']}\n" \
                       f"Grasa total: {item['Total Fat']}g ({item['Total Fat (% Daily Value)']}% del valor diario)\n" \
                       f"Sodio: {item['Sodium']}mg ({item['Sodium (% Daily Value)']}% del valor diario)\n" \
                       f"Carbohidratos: {item['Carbohydrates']}g ({item['Carbohydrates (% Daily Value)']}% del valor diario)\n" \
                       f"Proteínas: {item['Protein']}g"
    return "Lo siento, no pude encontrar información nutricional para ese artículo."

def start_order_process(query):
    st.session_state.order_in_progress = True
    item_name = query.split("de")[-1].strip().lower()
    for category, items in st.session_state.menu.items():
        for item in items:
            if item['Item'].lower() == item_name:
                st.session_state.current_order.append(item)
                return f"Has agregado {item['Item']} a tu pedido. ¿Deseas algo más?"
    return "No encontré ese producto en nuestro menú. Por favor, intenta nuevamente."

def cancel_order():
    if st.session_state.order_in_progress:
        st.session_state.current_order = []
        st.session_state.order_in_progress = False
        return "Tu pedido ha sido cancelado."
    else:
        return "No tienes un pedido en curso para cancelar."

def confirm_order():
    if st.session_state.order_in_progress and st.session_state.current_order:
        save_order_to_csv(st.session_state.current_order)
        st.session_state.order_in_progress = False
        st.session_state.current_order = []
        return "Tu pedido ha sido confirmado. ¡Gracias por tu compra!"
    else:
        return "No tienes un pedido en curso para confirmar."

def inform_total_price():
    return "Lo siento, no puedo proporcionar el precio total ya que no contamos con esa información."

def save_order_to_csv(order):
    filename = 'orders.csv'
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Date', 'Item']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for item in order:
            writer.writerow({
                'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Item': item['Item']
            })

def consult_delivery_cities(query):
    response = "Realizamos entregas en las siguientes ciudades:\n"
    for city in st.session_state.delivery_cities[:10]:  # Mostrar solo las primeras 10 ciudades
        response += f"- {city}\n"
    response += "... y más ciudades. ¿Hay alguna ciudad específica que te interese?"
    return response

def process_general_query(query):
    if openai_available:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente de restaurante amable y servicial."},
                    {"role": "user", "content": query}
                ],
                max_tokens=500
            )
            return response.choices[0].message['content']
        except Exception as e:
            st.error(f"Error al procesar la consulta: {e}")
            return "Lo siento, ocurrió un error al procesar tu consulta."
    else:
        return "Lo siento, no puedo procesar consultas generales en este momento debido a limitaciones técnicas."

def generate_response(query_result):
    if openai_available:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente de restaurante amable y servicial."},
                    {"role": "user", "content": f"Basado en la siguiente información: '{query_result}', genera una respuesta amigable y natural para un cliente de restaurante:"}
                ],
                max_tokens=150
            )
            return response.choices[0].message['content']
        except Exception as e:
            st.error(f"Error al generar la respuesta: {e}")
            return "Lo siento, ocurrió un error al generar la respuesta."
    else:
        return query_result

def main():
    st.title("Chatbot de Restaurante")

    if st.button("Inicializar Chatbot"):
        initialize_chatbot()

    user_message = st.text_input("Escribe tu mensaje aquí:")

    if st.button("Enviar"):
        if not moderate_content(user_message):
            st.error("Lo siento, tu mensaje no es apropiado. Por favor, intenta de nuevo.")
        else:
            query_result = process_user_query(user_message)
            response = generate_response(query_result)

            st.session_state.chat_history.append(("Usuario", user_message))
            st.session_state.chat_history.append(("Chatbot", response))

    st.subheader("Historial de Chat")
    for role, message in st.session_state.chat_history:
        st.write(f"**{role}:** {message}")

if __name__ == "__main__":
    main()
