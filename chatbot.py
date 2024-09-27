import streamlit as st
import csv
from datetime import datetime

# Inicialización de variables de estado de Streamlit
if 'menu' not in st.session_state:
    st.session_state.menu = {}
if 'delivery_districts' not in st.session_state:
    st.session_state.delivery_districts = []
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

def load_delivery_districts():
    try:
        with open('delivery_districts.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            st.session_state.delivery_districts = [row['District'] for row in reader]
    except FileNotFoundError:
        st.error("Error: No se encontró el archivo 'delivery_districts.csv'.")

def initialize_chatbot():
    load_menu_from_csv()
    load_delivery_districts()
    st.success("¡Chatbot inicializado exitosamente!")

def moderate_content(message):
    offensive_words = ['palabrota1', 'palabrota2', 'palabrota3']  # Agrega más si es necesario
    return not any(word in message.lower() for word in offensive_words)

def process_user_query(query):
    if "menú" in query.lower() or "carta" in query.lower():
        return show_menu()
    elif "pedir" in query.lower() or "ordenar" in query.lower():
        return start_order_process()
    elif "distrito" in query.lower() or "entrega" in query.lower():
        return show_delivery_districts()
    else:
        return "Lo siento, no entendí tu solicitud. Por favor, intenta nuevamente."

def show_menu():
    st.subheader("📋 Nuestro Menú")
    for category, items in st.session_state.menu.items():
        with st.expander(category):
            for item in items:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{item['Item']}**")
                    st.write(f"{item['Description']}")
                    st.write(f"Precio: ${item['Price']}")
                with col2:
                    if st.button(f"Añadir '{item['Item']}'", key=item['Item']):
                        st.session_state.order.append(item)
                        st.success(f"'{item['Item']}' ha sido añadido a tu pedido.")
    return "Puedes navegar por nuestro menú y añadir items a tu pedido."

def start_order_process():
    if not st.session_state.order:
        return "Tu carrito está vacío. Por favor, añade productos desde el menú."
    else:
        st.subheader("🛒 Tu Pedido")
        total_price = 0
        for item in st.session_state.order:
            st.write(f"- {item['Item']} - ${item['Price']}")
            total_price += float(item['Price'])
        st.write(f"**Total: ${total_price:.2f}**")
        if st.button("Confirmar Pedido"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"¡Gracias por tu pedido! Se ha confirmado a las {timestamp}.")
            st.session_state.order = []
        return "Aquí está el resumen de tu pedido."

def show_delivery_districts():
    st.subheader("🚚 Distritos de Entrega")
    for district in st.session_state.delivery_districts:
        st.write(f"- {district}")
    return "Estos son los distritos a los que realizamos entregas."

def main():
    st.title("🍽️ Chatbot de Restaurante")
    st.image("https://i.imgur.com/3ZQ3Z4K.jpg", use_column_width=True)
    st.write("¡Bienvenido a nuestro restaurante virtual! Estoy aquí para ayudarte con el menú, tomar tu pedido y proporcionar información sobre nuestras zonas de entrega.")

    if st.button("Inicializar Chatbot"):
        initialize_chatbot()

    st.write("---")
    user_message = st.text_input("Escribe tu mensaje aquí:")

    if st.button("Enviar"):
        if not moderate_content(user_message):
            st.error("Lo siento, tu mensaje no es apropiado. Por favor, intenta de nuevo.")
        else:
            response = process_user_query(user_message)
            st.session_state.chat_history.append(("Usuario", user_message))
            st.session_state.chat_history.append(("Chatbot", response))
            st.write(response)

    st.write("---")
    st.subheader("💬 Historial de Chat")
    for role, message in st.session_state.chat_history:
        if role == "Usuario":
            st.markdown(f"**{role}:** {message}")
        else:
            st.markdown(f"**{role}:** {message}")

if __name__ == "__main__":
    main()
