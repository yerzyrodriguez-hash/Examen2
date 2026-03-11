# app/chatbot.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
import google.generativeai as genai
from .models import Libro, User
from .extensions import db

chatbot_bp = Blueprint('chatbot', __name__)
genai.configure(api_key="AIzaSyDhgRpAfQh-XMqgDpIVzIsQg4be9u15aag")
modelo = genai.GenerativeModel('gemini-2.5-flash')

@chatbot_bp.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    datos = request.get_json()
    pregunta = datos.get('pregunta', '')

    if not pregunta:
        return jsonify({'respuesta': 'Por favor, hazme una pregunta.'})

    try:
        libros = Libro.query.all()
        if libros:
            contexto_libros = "\n".join([f"- '{l.titulo}' por {l.autor} (Categoría: {l.categoria.nombre if l.categoria else 'General'} | Stock: {l.stock})" for l in libros])
        else:
            contexto_libros = "No hay libros registrados."
        from .models import Prestamo
        prestamos = Prestamo.query.filter_by(estado="Pendiente").all()
        if prestamos:
            contexto_prestamos = "\n".join([f"- El libro '{p.libro.titulo}' está prestado a {p.usuario.perfil.nombre} (Fecha: {p.fecha_prestamo.strftime('%Y-%m-%d')})" for p in prestamos])
        else:
            contexto_prestamos = "Actualmente no hay libros prestados o reservas pendientes."
        prompt_sistema = f"""
        Eres el bibliotecario experto de nuestro sistema. 
        Aquí tienes la información EN TIEMPO REAL de la base de datos:
        
        📚 CATÁLOGO DE LIBROS:
        {contexto_libros}

        📋 PRÉSTAMOS ACTIVOS (RESERVAS):
        {contexto_prestamos}

        El usuario te pregunta: "{pregunta}"
        
        Instrucciones:
        - Responde de forma natural, amigable y muy útil.
        - Si te piden recomendaciones, usa las categorías o el autor para sugerir.
        - Si te preguntan por reservas o préstamos, usa la sección de Préstamos Activos.
        - No inventes libros que no estén en la lista.
        """

        respuesta_ia = modelo.generate_content(prompt_sistema)
        return jsonify({'respuesta': respuesta_ia.text})

    except Exception as e:
        print(f"Error del chatbot: {e}")
        return jsonify({'respuesta': 'Lo siento, tuve un problema conectándome a mi cerebro. Avisa al administrador.'})