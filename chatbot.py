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
if 'order' not in st.session_state:
    st.session_state.order = []

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
        st.error("Error: El archivo 'menu.csv' no se encontró.")

def load_delivery_cities():
    try:
        with open('us-cities.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            st.session_state.delivery_cities = [f"{row['City']}, {row['State short']}" for row in reader]
    except FileNotFoundError:
        st.error("Error: El archivo 'us-cities.csv' no se encontró.")

def initialize_chatbot():
    load_menu_from_csv()
    load_delivery_cities()
    st.success("¡Chatbot inicializado exitosamente!")

def moderate_content(message):
    offensive_words = ['palabrota1', 'palabrota2', 'palabrota3']  # Agrega más si es necesario
    return not any(word in message.lower() for word in offensive_words)

def process_user_query(query):
    if "menú" in query.lower() or "carta" in query.lower():
        return show_menu()
    elif "pedir" in query.lower() or "ordenar" in query.lower():
        return start_order_process()
    elif "entrega" in query.lower() or "reparto" in query.lower():
        return consult_delivery_cities()
    elif "información nutricional" in query.lower() or "calorías" in query.lower():
        return get_nutritional_info(query)
    else:
        return process_general_query(query)

def show_menu():
    st.subheader("Nuestro Menú")
    for category, items in st.session_state.menu.items():
        with st.expander(category):
            for item in items:
                st.markdown(f"**{item['Item']}**")
                st.write(f"Tamaño de porción: {item['Serving Size']}")
                st.write(f"Calorías: {item['Calories']}")
                if st.button(f"Añadir {item['Item']} a la orden", key=item['Item']):
                    st.session_state.order.append(item)
                    st.success(f"{item['Item']} añadido a tu orden.")
    return "Por favor, revisa nuestro menú y selecciona los ítems que deseas ordenar."

def get_nutritional_info(query):
    item_name = query.split("de ")[-1].strip().lower()
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

def start_order_process():
    if not st.session_state.order:
        return "No tienes ningún ítem en tu orden. Por favor, añade ítems desde el menú."
    else:
        total_items = len(st.session_state.order)
        total_calories = sum(int(item['Calories']) for item in st.session_state.order)
        order_details = "\n".join([f"- {item['Item']}" for item in st.session_state.order])
        return f"Tienes {total_items} ítem(s) en tu orden:\n{order_details}\nCalorías totales: {total_calories}"

def consult_delivery_cities():
    response = "Realizamos entregas en las siguientes ciudades:\n"
    for city in st.session_state.delivery_cities[:10]:  # Mostrar solo las primeras 10 ciudades
        response += f"- {city}\n"
    response += "... y más ciudades. ¿Hay alguna ciudad específica que te interese?"
    return response

def process_general_query(query):
    if openai_available:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Modelo de OpenAI para chat
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
    st.set_page_config(page_title="Chatbot de Restaurante", page_icon="🍽️")
    st.title("🍽️ Chatbot de Restaurante")
    st.image("https://i.imgur.com/3ZQ3Z4K.jpg", use_column_width=True)

    if st.button("Inicializar Chatbot"):
        initialize_chatbot()

    st.write("---")
    user_message = st.text_input("Escribe tu mensaje aquí:")

    if st.button("Enviar"):
        if not moderate_content(user_message):
            st.error("Lo siento, tu mensaje no es apropiado. Por favor, intenta de nuevo.")
        else:
            query_result = process_user_query(user_message)
            response = generate_response(query_result)
            st.session_state.chat_history.append(("Usuario", user_message))
            st.session_state.chat_history.append(("Chatbot", response))
            st.success(response)

    st.write("---")
    if st.session_state.order:
        st.subheader("🛒 Tu Orden")
        for item in st.session_state.order:
            st.write(f"- {item['Item']}")
        if st.button("Finalizar Pedido"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"¡Gracias por tu pedido! Número de orden: {random.randint(1000,9999)} - Timestamp: {timestamp}")
            st.session_state.order = []
    else:
        st.info("Tu carrito está vacío.")

    st.write("---")
    st.subheader("💬 Historial de Chat")
    for role, message in st.session_state.chat_history:
        if role == "Usuario":
            st.markdown(f"**{role}:** {message}")
        else:
            st.markdown(f"**{role}:** {message}")

if __name__ == "__main__":
    main()

