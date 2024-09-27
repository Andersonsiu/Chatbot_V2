import streamlit as st
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
        st.error("Error: menu.csv file not found.")

def load_delivery_cities():
    try:
        with open('us-cities.csv', 'r', encoding='utf-8') as file:
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
        return show_menu()
    elif "pedir" in query.lower() or "ordenar" in query.lower() or "quiero" in query.lower():
        return take_order(query)
    elif "entrega" in query.lower() or "reparto" in query.lower():
        return consult_delivery_cities(query)
    elif "información nutricional" in query.lower() or "calorías" in query.lower():
        return get_nutritional_info(query)
    else:
        return process_general_query(query)

def show_menu():
    response = "Aquí está nuestro menú del día:\n\n"
    for category, items in st.session_state.menu.items():
        response += f"**{category}**\n"
        for item in items:
            response += f"- {item['Item']}: {item['Description']} (${item['Price']})\n"
        response += "\n"
    return response

def get_nutritional_info(query):
    item_name = query.lower().split("de")[-1].strip()
    for category, items in st.session_state.menu.items():
        for item in items:
            if item['Item'].lower() == item_name:
                return f"Información nutricional para {item['Item']}:\n" \
                       f"Tamaño de porción: {item['Serving Size']}\n" \
                       f"Calorías: {item['Calories']}\n" \
                       f"Grasa total: {item['Total Fat']}g ({item['Total Fat (% Daily Value)']}% VD)\n" \
                       f"Sodio: {item['Sodium']}mg ({item['Sodium (% Daily Value)']}% VD)\n" \
                       f"Carbohidratos: {item['Carbohydrates']}g ({item['Carbohydrates (% Daily Value)']}% VD)\n" \
                       f"Proteínas: {item['Protein']}g"
    return "Lo siento, no encontré información nutricional para ese artículo."

def take_order(query):
    # Extraer nombres de ítems del pedido
    ordered_items = []
    for category, items in st.session_state.menu.items():
        for item in items:
            if item['Item'].lower() in query.lower():
                ordered_items.append(item)

    if ordered_items:
        st.session_state.order.extend(ordered_items)
        items_list = ', '.join([item['Item'] for item in ordered_items])
        return f"Has pedido: {items_list}. ¿Deseas algo más?"
    else:
        return "No pude identificar los ítems que deseas pedir. Por favor, menciona los nombres exactos de los platos."

def consult_delivery_cities(query):
    response = "Realizamos entregas en las siguientes ciudades:\n"
    for city in st.session_state.delivery_cities[:10]:  # Mostrar solo las primeras 10 ciudades
        response += f"- {city}\n"
    response += "¿Hay alguna ciudad específica que te interese?"
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
                max_tokens=150
            )
            return response.choices[0].message['content']
        except Exception as e:
            st.error(f"Error al procesar la consulta: {e}")
            return "Lo siento, ocurrió un error al procesar tu consulta."
    else:
        return "Lo siento, no puedo procesar consultas generales en este momento debido a limitaciones técnicas."

def generate_response(query_result):
    return query_result

def main():
    st.title("🍽️ Chatbot de Restaurante")
    st.write("¡Bienvenido! Soy tu asistente virtual. Puedes pedirme el menú, hacer un pedido o consultar sobre entregas.")

    if st.button("Inicializar Chatbot"):
        initialize_chatbot()

    st.write("---")
    user_message = st.text_input("Escribe tu mensaje:", key="user_input")

    if st.button("Enviar", key="send_button"):
        if not moderate_content(user_message):
            st.error("Lo siento, tu mensaje no es apropiado. Por favor, intenta de nuevo.")
        else:
            query_result = process_user_query(user_message)
            response = generate_response(query_result)

            st.session_state.chat_history.append(("Usuario", user_message))
            st.session_state.chat_history.append(("Chatbot", response))

    st.write("---")
    st.subheader("💬 Historial de Chat")
    for role, message in st.session_state.chat_history:
        if role == "Usuario":
            st.markdown(f"**{role}:** {message}")
        else:
            st.markdown(f"**{role}:** {message}")

    # Mostrar el resumen del pedido si hay artículos
    if st.session_state.order:
        st.write("---")
        st.subheader("🛒 Resumen de tu Pedido")
        total = 0
        for item in st.session_state.order:
            st.write(f"- {item['Item']} (${item['Price']})")
            total += float(item['Price'])
        st.write(f"**Total a pagar: ${total:.2f}**")
        if st.button("Confirmar Pedido", key="confirm_order"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"¡Gracias por tu pedido! Se ha confirmado a las {timestamp}.")
            st.session_state.order = []

if __name__ == "__main__":
    main()
