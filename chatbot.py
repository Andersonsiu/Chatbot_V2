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
        with open('menu.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = row['Category']
                if category not in st.session_state.menu:
                    st.session_state.menu[category] = []
                st.session_state.menu[category].append(row)
    except FileNotFoundError:
        st.error("Error: menu.csv file not found.")

def load_delivery_cities():
    try:
        with open('us-cities.csv', 'r') as file:
            reader = csv.DictReader(file)
            st.session_state.delivery_cities = [f"{row['City']}, {row['State short']}" for row in reader]
    except FileNotFoundError:
        st.error("Error: us-cities.csv file not found.")

def initialize_chatbot():
    load_menu_from_csv()
    load_delivery_cities()
    st.success("¡Chatbot inicializado exitosamente!")

def moderate_content(message):
    offensive_words = ['palabrota1', 'palabrota2', 'palabrota3']  # Agrega más si es necesario
    return not any(word in message.lower() for word in offensive_words)

def process_user_query(query):
    if "menú" in query.lower() or "carta" in query.lower():
        consult_menu_csv()
        return None  # No se necesita generar una respuesta adicional
    elif "pedir" in query.lower() or "ordenar" in query.lower():
        start_order_process()
        return None
    elif "entrega" in query.lower() or "reparto" in query.lower():
        return consult_delivery_cities(query)
    elif "información nutricional" in query.lower() or "calorías" in query.lower():
        return get_nutritional_info(query)
    else:
        return process_general_query(query)

def consult_menu_csv():
    st.subheader("📋 Menú del Día")
    for category, items in st.session_state.menu.items():
        st.write(f"**{category}**")
        for item in items:
            st.write(f"- {item['Item']}: {item['Serving Size']}, {item['Calories']} calorías")
    st.write("Para realizar un pedido, escribe 'quiero ordenar' y sigue las instrucciones.")

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
    st.subheader("🛒 Realizar Pedido")
    selected_items = []
    for category, items in st.session_state.menu.items():
        st.write(f"**{category}**")
        for item in items:
            if st.checkbox(f"{item['Item']} ({item['Serving Size']}, {item['Calories']} calorías)", key=item['Item']):
                selected_items.append(item)

    if st.button("Confirmar Pedido"):
        if selected_items:
            st.session_state.order.extend(selected_items)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Orden registrada: {[item['Item'] for item in selected_items]} - Timestamp: {timestamp}")
        else:
            st.warning("No has seleccionado ningún artículo.")

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
    if query_result is None:
        return  # No se necesita generar respuesta
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
    st.title("🍽️ Chatbot de Restaurante")

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
            if response:
                st.session_state.chat_history.append(("Chatbot", response))
                st.write(response)

    st.subheader("💬 Historial de Chat")
    for role, message in st.session_state.chat_history:
        st.write(f"**{role}:** {message}")

    if st.session_state.order:
        st.subheader("✅ Tu Pedido")
        for item in st.session_state.order:
            st.write(f"- {item['Item']}")
        if st.button("Finalizar Pedido"):
            st.success("¡Gracias por tu pedido! Pronto lo recibirás.")
            st.session_state.order = []

if __name__ == "__main__":
    main()
