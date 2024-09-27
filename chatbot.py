import streamlit as st
import csv
from datetime import datetime

# Inicialización de variables de estado de Streamlit
if 'menu' not in st.session_state:
    st.session_state.menu = {}
if 'delivery_cities' not in st.session_state:
    st.session_state.delivery_cities = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

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
        st.error("Error: No se encontró el archivo 'menu.csv'.")

def load_delivery_cities():
    try:
        with open('us-cities.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            st.session_state.delivery_cities = [f"{row['City']}, {row['State short']}" for row in reader]
    except FileNotFoundError:
        st.error("Error: No se encontró el archivo 'us-cities.csv'.")

def initialize_chatbot():
    load_menu_from_csv()
    load_delivery_cities()
    st.session_state.chat_history.append(("Chatbot", "¡Hola! Soy tu asistente virtual de restaurante. ¿En qué puedo ayudarte hoy?"))

def moderate_content(message):
    offensive_words = ['palabrota1', 'palabrota2', 'palabrota3']  # Agrega más si es necesario
    return not any(word in message.lower() for word in offensive_words)

def process_user_query(query):
    if "menú" in query.lower() or "carta" in query.lower():
        return consult_menu()
    elif "pedir" in query.lower() or "ordenar" in query.lower():
        return start_order_process(query)
    elif "entrega" in query.lower() or "reparto" in query.lower():
        return consult_delivery_cities()
    elif "información nutricional" in query.lower() or "calorías" in query.lower():
        return get_nutritional_info(query)
    else:
        return "Lo siento, no entendí tu solicitud. ¿Podrías reformularla, por favor?"

def consult_menu():
    response = "Aquí está nuestro menú:\n\n"
    for category, items in st.session_state.menu.items():
        response += f"**{category}**\n"
        for item in items:
            response += f"- {item['Item']}: {item['Serving Size']}, {item['Calories']} calorías\n"
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

def start_order_process(query):
    # Simulación de registro de orden
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Hemos registrado tu pedido. Número de orden: {random.randint(1000,9999)} - Timestamp: {timestamp}"

def consult_delivery_cities():
    response = "Realizamos entregas en las siguientes ciudades:\n"
    for city in st.session_state.delivery_cities[:10]:  # Mostrar solo las primeras 10 ciudades
        response += f"- {city}\n"
    response += "... y más ciudades. ¿Hay alguna ciudad específica que te interese?"
    return response

def main():
    st.set_page_config(page_title="Chatbot de Restaurante", page_icon="🍽️")
    st.markdown(
        """
        <style>
        .chat-bubble {
            background-color: #F1F0F0;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            width: fit-content;
        }
        .user-message {
            background-color: #DCF8C6;
            align-self: flex-end;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🍽️ Chatbot de Restaurante")
    st.write("¡Bienvenido! Estoy aquí para ayudarte con tu pedido. Pregúntame sobre el menú, realiza un pedido o consulta nuestras zonas de entrega.")

    if 'initialized' not in st.session_state:
        initialize_chatbot()
        st.session_state.initialized = True

    # Mostrar historial de chat
    chat_placeholder = st.container()
    with chat_placeholder:
        for role, message in st.session_state.chat_history:
            if role == "Usuario":
                st.markdown(f"<div class='chat-bubble user-message'><strong>{role}:</strong> {message}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bubble'><strong>{role}:</strong> {message}</div>", unsafe_allow_html=True)

    # Input de usuario con botón enviar
    st.write("---")
    with st.form(key='user_input_form', clear_on_submit=True):
        user_message = st.text_input("Escribe tu mensaje aquí:")
        submitted = st.form_submit_button("Enviar")
    if submitted:
        if user_message:
            if not moderate_content(user_message):
                st.error("Lo siento, tu mensaje no es apropiado. Por favor, intenta de nuevo.")
            else:
                st.session_state.chat_history.append(("Usuario", user_message))
                response = process_user_query(user_message)
                st.session_state.chat_history.append(("Chatbot", response))
                st.experimental_rerun()

if __name__ == "__main__":
    main()
