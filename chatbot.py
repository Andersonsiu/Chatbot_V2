import streamlit as st
import os
import csv
from datetime import datetime

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

def initialize_chatbot():
    load_menu_from_csv()
    st.success("¡Chatbot inicializado exitosamente!")

def moderate_content(message):
    offensive_words = ['palabrota1', 'palabrota2', 'palabrota3']  # Agrega más si es necesario
    return not any(word in message.lower() for word in offensive_words)

def process_user_query(query):
    if "menú" in query.lower() or "carta" in query.lower():
        return consult_menu_csv()
    elif "pedir" in query.lower() or "ordenar" in query.lower():
        return start_order_process(query)
    elif "cancelar" in query.lower() or "anular" in query.lower():
        return cancel_order()
    elif "confirmar" in query.lower():
        return confirm_order()
    else:
        return process_general_query(query)

def consult_menu_csv():
    response = "Aquí está nuestro menú:\n\n"
    for category, items in st.session_state.menu.items():
        response += f"{category}:\n"
        for item in items:
            response += f"- {item['Item']}: {item['Serving Size']}, Precio: ${item['Price']}\n"
        response += "\n"
    return response

def start_order_process(query):
    # Buscar el ítem en el menú basado en la consulta del usuario
    item_name = query.split("de")[-1].strip().lower()
    for category, items in st.session_state.menu.items():
        for item in items:
            if item['Item'].lower() == item_name:
                st.session_state.current_order.append(item)
                st.session_state.order_in_progress = True
                return f"Has agregado **{item['Item']}** a tu pedido por un precio de ${item['Price']}. ¿Deseas algo más?"
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
        total_price = sum(float(item['Price']) for item in st.session_state.current_order)
        save_order_to_csv(st.session_state.current_order)
        st.session_state.order_in_progress = False
        st.session_state.current_order = []
        return f"Tu pedido ha sido confirmado. El precio total es ${total_price:.2f}. ¡Gracias por tu compra!"
    else:
        return "No tienes un pedido en curso para confirmar."

def save_order_to_csv(order):
    filename = 'orders.csv'
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Category', 'Item', 'Serving Size', 'Price', 'Timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for item in order:
            writer.writerow({
                'Category': item['Category'],
                'Item': item['Item'],
                'Serving Size': item['Serving Size'],
                'Price': item['Price'],
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

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
    return query_result

def main():
    st.set_page_config(page_title="Chatbot de Restaurante", page_icon="🍽️", layout="wide")
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
            st.session_state.chat_history.append(("Chatbot", response))

    # Mostrar historial de chat
    st.subheader("Historial de Chat")
    chat_container = st.container()
    with chat_container:
        for role, message in st.session_state.chat_history:
            if role == "Usuario":
                st.markdown(
                    f"<div style='text-align: right; background-color: #add8e6; padding: 10px; border-radius: 10px; margin: 5px;'>{message}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align: left; background-color: #ffe4b5; padding: 10px; border-radius: 10px; margin: 5px;'>{message}</div>",
                    unsafe_allow_html=True
                )

    # Mostrar el pedido actual y el precio total
    if st.session_state.current_order:
        st.markdown("### Pedido Actual")
        order_items = [f"{item['Item']} - ${item['Price']}" for item in st.session_state.current_order]
        st.write(", ".join(order_items))
        total_price = sum(float(item['Price']) for item in st.session_state.current_order)
        st.write(f"**Precio Total:** ${total_price:.2f}")

    st.markdown("---")
    st.markdown("**Restaurante Sabores Deliciosos** | Teléfono: (123) 456-7890 | Dirección: Calle Falsa 123, Ciudad Gourmet")

if __name__ == "__main__":
    main()

