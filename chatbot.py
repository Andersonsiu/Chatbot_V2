import streamlit as st
import os
import csv
import random
from datetime import datetime

try:
    import openai
    openai_available = True
except ImportError:
    st.error("Error: La librería 'openai' no está instalada. Algunas funcionalidades no estarán disponibles.")
    openai_available = False

# Inicializar OpenAI solo si está disponible
if openai_available:
    openai.api_key = st.secrets.get("OPENAI_API_KEY", "")

# Inicialización de variables de estado de Streamlit
if 'menu' not in st.session_state:
    st.session_state['menu'] = {}
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'current_order' not in st.session_state:
    st.session_state['current_order'] = []
if 'order_in_progress' not in st.session_state:
    st.session_state['order_in_progress'] = False

def load_menu_from_csv(filepath='menu.csv'):
    if os.path.isfile(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    category = row['Category']
                    if category not in st.session_state.menu:
                        st.session_state.menu[category] = []
                    st.session_state.menu[category].append(row)
            st.success("Menú cargado exitosamente.")
        except Exception as e:
            st.error(f"Error al cargar el menú: {e}")
    else:
        st.error(f"Error: El archivo '{filepath}' no fue encontrado.")

def moderate_content(message):
    offensive_words = ['palabrota1', 'palabrota2', 'palabrota3']  # Agrega más palabras si es necesario
    return not any(word in message.lower() for word in offensive_words)

def is_invalid_request(query):
    # Detectar si la consulta es inválida o no deseada
    invalid_phrases = [
        "descuento", "cambiar el costo", "neumático", "ticket de bus",
        "un millón", "mil unidades", "plato que no esté en la carta"
    ]
    return any(phrase in query for phrase in invalid_phrases) or not moderate_content(query)

def process_user_query(query):
    query = query.lower().strip()
    
    # Si la consulta es inválida, responder de forma genérica
    if is_invalid_request(query):
        return "Lo siento, no puedo procesar esa solicitud. Por favor, intenta con una consulta válida relacionada con el menú del restaurante."
    
    # Manejar preguntas válidas
    if "menú" in query or "carta" in query:
        return consult_menu_csv()
    elif "precio" in query and "productos" in query:
        return show_random_product_prices(3)
    elif "ordenar" in query or "pedir" in query:
        return start_order_process(query)
    elif any(word in query for word in ["cancelar", "anular", "ya no deseo mi orden"]):
        return cancel_order()
    elif any(word in query for word in ["beber", "gaseosa", "bebidas"]):
        return suggest_drinks()
    else:
        return "Lo siento, no entendí tu solicitud. ¿Podrías reformular tu pregunta?"

def consult_menu_csv():
    response = "Aquí está nuestro menú:\n\n"
    for category, items in st.session_state.menu.items():
        response += f"**{category}**:\n"
        for item in items:
            response += f"- {item['Item']}: {item['Serving Size']}, Precio: ${item['Price']}\n"
        response += "\n"
    return response

def show_random_product_prices(count=3):
    all_items = [item for category in st.session_state.menu.values() for item in category]
    if len(all_items) == 0:
        return "Lo siento, no hay productos disponibles para mostrar precios."
    
    random_items = random.sample(all_items, min(count, len(all_items)))
    response = "Aquí están los precios de algunos productos:\n\n"
    for item in random_items:
        response += f"- {item['Item']}: ${item['Price']}\n"
    return response

def suggest_drinks():
    drinks = [item for category, items in st.session_state.menu.items() if 'bebida' in category.lower() or 'gaseosa' in item['Item'].lower() for item in items]
    if drinks:
        response = "Estas son las bebidas que tenemos disponibles:\n\n"
        for drink in drinks:
            response += f"- {drink['Item']}: ${drink['Price']}\n"
    else:
        response = "Lo siento, no tenemos bebidas disponibles en este momento."
    return response

def start_order_process(query):
    # Intentar extraer el nombre del producto y la cantidad
    words = query.split()
    quantity = 1
    try:
        for i in range(len(words)):
            if words[i].isdigit():
                quantity = int(words[i])
                break
    except ValueError:
        quantity = 1

    item_name = ' '.join(words).split("de")[-1].strip()
    found_item = None

    # Buscar el ítem en el menú
    for category, items in st.session_state.menu.items():
        for item in items:
            if item['Item'].lower() == item_name:
                found_item = item
                break

    if found_item:
        total_price = float(found_item['Price']) * quantity
        st.session_state.current_order.append({
            'Category': found_item['Category'],
            'Item': found_item['Item'],
            'Serving Size': found_item['Serving Size'],
            'Price': total_price,
            'Quantity': quantity
        })
        st.session_state.order_in_progress = True
        return f"Has agregado {quantity} **{found_item['Item']}** a tu pedido por un precio total de ${total_price:.2f}. ¿Deseas algo más?"
    else:
        return "Lo siento, no encontré ese producto en nuestro menú. Por favor, intenta con otro artículo."

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

def save_order_to_csv(order, filename='orders.csv'):
    file_exists = os.path.isfile(filename)
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Category', 'Item', 'Serving Size', 'Price', 'Quantity', 'Timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for item in order:
                writer.writerow({
                    'Category': item['Category'],
                    'Item': item['Item'],
                    'Serving Size': item['Serving Size'],
                    'Price': item['Price'],
                    'Quantity': item['Quantity'],
                    'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
    except Exception as e:
        st.error(f"Error al guardar el pedido: {e}")

def display_chat_history():
    st.markdown("### 🗨️ Historial de Chat")
    chat_container = st.container()
    with chat_container:
        for role, message in st.session_state.chat_history:
            if role == "Usuario":
                st.markdown(
                    f"<div style='text-align: right; background-color: #d1e7ff; color: black; padding: 10px; border-radius: 15px; margin: 5px 10px 5px 50px; max-width: 70%;'>{message}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align: left; background-color: #ffeeba; color: black; padding: 10px; border-radius: 15px; margin: 5px 50px 5px 10px; max-width: 70%;'>{message}</div>",
                    unsafe_allow_html=True
                )

def main():
    st.set_page_config(page_title="Chatbot de Restaurante", page_icon="🍽️", layout="wide")
    st.markdown("<h1 style='text-align: center; color: #ff6347;'>🍽️ Chatbot de Restaurante 🍽️</h1>", unsafe_allow_html=True)

    if st.button("Inicializar Chatbot"):
        load_menu_from_csv()

    user_message = st.text_input("Escribe tu mensaje aquí:", key="user_input", placeholder="¿Qué te gustaría pedir hoy?")
    send_button = st.button("Enviar")

    if send_button and user_message:
        query_result = process_user_query(user_message)
        st.session_state.chat_history.append(("Usuario", user_message))
        st.session_state.chat_history.append(("Chatbot", query_result))

    # Mostrar historial de chat con burbujas
    display_chat_history()

    # Mostrar el pedido actual y el precio total
    if st.session_state.current_order:
        st.markdown("### 🛒 Pedido Actual")
        order_items = [f"{item['Item']} x{item['Quantity']} - ${item['Price']}" for item in st.session_state.current_order]
        st.write(", ".join(order_items))
        total_price = sum(float(item['Price']) for item in st.session_state.current_order)
        st.write(f"**Precio Total:** ${total_price:.2f}")

    # Información del restaurante en el pie de página
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #ff6347;'>Restaurante Sabores Deliciosos | Teléfono: (123) 456-7890 | Dirección: Calle Falsa 123, Ciudad Gourmet</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
