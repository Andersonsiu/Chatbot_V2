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
    offensive_words = ['palabrota1', 'palabrota2', 'palabrota3']
    return not any(word in message.lower() for word in offensive_words)

def process_user_query(query):
    if "menú" in query.lower() or "carta" in query.lower():
        return show_menu()
    elif "pedir" in query.lower() or "ordenar" in query.lower() or "quiero" in query.lower():
        return take_order(query)
    elif "entrega" in query.lower() or "reparto" in query.lower():
        return consult_delivery_cities()
    elif "información nutricional" in query.lower() or "calorías" in query.lower():
        return get_nutritional_info(query)
    else:
        return "Lo siento, no entendí tu solicitud. ¿Podrías reformularla, por favor?"

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
                       f"Grasa total: {item['Total Fat']}g\n" \
                       f"Sodio: {item['Sodium']}mg\n" \
                       f"Carbohidratos: {item['Carbohydrates']}g\n" \
                       f"Proteínas: {item['Protein']}g"
    return "Lo siento, no encontré información nutricional para ese artículo."

def take_order(query):
    ordered_items = []
    for category, items in st.session_state.menu.items():
        for item in items:
            if item['Item'].lower() in query.lower():
                ordered_items.append(item)

    if ordered_items:
        st.session_state.order.extend(ordered_items)
        items_list = ', '.join([item['Item'] for item in ordered_items])
        return f"Has añadido a tu pedido: {items_list}. ¿Deseas algo más?"
    else:
        return "No pude identificar los ítems que deseas pedir. Por favor, menciona los nombres exactos de los platos."

def consult_delivery_cities():
    response = "Realizamos entregas en las siguientes ciudades:\n"
    for city in st.session_state.delivery_cities[:10]:
        response += f"- {city}\n"
    response += "¿Hay alguna ciudad específica que te interese?"
    return response

def main():
    st.title("🍽️ Chatbot de Restaurante")
    st.write("Bienvenido al chatbot de restaurante. Puedes preguntar por el menú, hacer un pedido o consultar nuestras zonas de entrega.")

    if 'initialized' not in st.session_state:
        initialize_chatbot()
        st.session_state.initialized = True

    # Mostrar historial de chat
    for role, message in st.session_state.chat_history:
        if role == "Usuario":
            st.markdown(f"**{role}:** {message}")
        else:
            st.markdown(f"**{role}:** {message}")

    # Input de usuario estilo chat
    user_message = st.text_input("Escribe tu mensaje aquí:", key=str(datetime.now()))
    if user_message:
        if not moderate_content(user_message):
            st.error("Lo siento, tu mensaje no es apropiado. Por favor, intenta de nuevo.")
        else:
            st.session_state.chat_history.append(("Usuario", user_message))
            response = process_user_query(user_message)
            st.session_state.chat_history.append(("Chatbot", response))
            st.experimental_rerun()  # Actualiza la interfaz para mostrar el nuevo mensaje

    # Mostrar resumen del pedido si hay artículos
    if st.session_state.order:
        st.write("---")
        st.subheader("🛒 Resumen de tu Pedido")
        total = 0
        for item in st.session_state.order:
            st.write(f"- {item['Item']} (${item['Price']})")
            total += float(item['Price'])
        st.write(f"**Total a pagar: ${total:.2f}**")
        if st.button("Confirmar Pedido"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"¡Gracias por tu pedido! Se ha confirmado a las {timestamp}.")
            st.session_state.order = []
            st.session_state.chat_history.append(("Chatbot", "¡Tu pedido ha sido confirmado!"))
            st.experimental_rerun()

if __name__ == "__main__":
    main()
