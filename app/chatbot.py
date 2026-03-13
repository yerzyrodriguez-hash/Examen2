# app/chatbot.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime
from sqlalchemy import func
import google.generativeai as genai
from .models import Libro, User, Prestamo, Categoria
from .extensions import db

chatbot_bp = Blueprint('chatbot', __name__)
genai.configure(api_key="AIzaSyDhgRpAfQh-XMqgDpIVzIsQg4be9u15aag")
modelo = genai.GenerativeModel('gemini-2.5-flash')


# ──────────────────────────────────────────
#  CHATBOT  (tuyo)
# ──────────────────────────────────────────
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
            contexto_libros = "\n".join([
                f"- '{l.titulo}' por {l.autor} (Categoría: {l.categoria.nombre if l.categoria else 'General'} | Stock: {l.stock})"
                for l in libros
            ])
        else:
            contexto_libros = "No hay libros registrados."

        prestamos = Prestamo.query.filter_by(estado="Pendiente").all()
        if prestamos:
            contexto_prestamos = "\n".join([
                f"- El libro '{p.libro.titulo}' está prestado a {p.usuario.perfil.nombre} (Fecha: {p.fecha_prestamo.strftime('%Y-%m-%d')})"
                for p in prestamos
            ])
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


# ──────────────────────────────────────────
#  ANÁLISIS IA DEL DASHBOARD  (Kevin)
# ──────────────────────────────────────────
@chatbot_bp.route('/api/analisis-ia', methods=['GET'])
@login_required
def analisis_ia():
    mes_actual  = datetime.now().month
    anio_actual = datetime.now().year

    nombres_meses = {
        1:"Enero",     2:"Febrero",   3:"Marzo",      4:"Abril",
        5:"Mayo",      6:"Junio",     7:"Julio",       8:"Agosto",
        9:"Septiembre",10:"Octubre",  11:"Noviembre",  12:"Diciembre"
    }

    # ── Datos generales ──
    total_libros        = Libro.query.count()
    total_usuarios      = User.query.count()
    prestamos_activos   = Prestamo.query.filter_by(estado="Pendiente").all()
    prestamos_devueltos = Prestamo.query.filter_by(estado="Devuelto").all()

    # ── Top 5 libros más prestados ──
    top_libros = db.session.query(
        Libro.titulo,
        Libro.stock,
        func.count(Prestamo.id).label('veces')
    ).join(Prestamo, Prestamo.libro_id == Libro.id) \
     .group_by(Libro.id, Libro.titulo, Libro.stock) \
     .order_by(func.count(Prestamo.id).desc()) \
     .limit(5).all()

    # ── Préstamos por mes — func.month() es la función correcta en MySQL ──
    prestamos_por_mes = db.session.query(
        func.month(Prestamo.fecha_prestamo).label('mes'),
        func.count(Prestamo.id).label('total')
    ).group_by(func.month(Prestamo.fecha_prestamo)) \
     .order_by(func.month(Prestamo.fecha_prestamo)) \
     .all()

    # ── Categorías más populares ──
    categorias_stats = db.session.query(
        Categoria.nombre,
        func.count(Libro.id).label('total')
    ).join(Libro, Libro.categoria_id == Categoria.id) \
     .group_by(Categoria.id, Categoria.nombre) \
     .order_by(func.count(Libro.id).desc()).all()

    # ── Top 5 usuarios más activos ──
    top_usuarios = db.session.query(
        User.username,
        func.count(Prestamo.id).label('total')
    ).join(Prestamo, Prestamo.usuario_id == User.id) \
     .group_by(User.id, User.username) \
     .order_by(func.count(Prestamo.id).desc()) \
     .limit(5).all()

    # ── Libros con stock crítico (≤2) ──
    libros_stock_bajo = Libro.query.filter(Libro.stock <= 2).all()

    # ── Construir textos de contexto ──
    contexto_top_libros = "\n".join([
        f"  • '{t}' - prestado {v} veces | Stock actual: {s} unidades"
        for t, s, v in top_libros
    ]) or "Sin datos"

    contexto_prestamos_mes = "\n".join([
        f"  • {nombres_meses.get(m, m)}: {c} préstamos"
        for m, c in prestamos_por_mes
    ]) or "Sin datos"

    contexto_categorias = "\n".join([
        f"  • {n}: {t} libros"
        for n, t in categorias_stats
    ]) or "Sin datos"

    contexto_top_usuarios = "\n".join([
        f"  • {u}: {t} préstamos realizados"
        for u, t in top_usuarios
    ]) or "Sin datos"

    contexto_stock_bajo = "\n".join([
        f"  • '{l.titulo}' - solo {l.stock} unidad(es) disponible(s)"
        for l in libros_stock_bajo
    ]) or "Ninguno"

    # ── Estación / época escolar boliviana ──
    if mes_actual in [12, 1, 2]:
        estacion          = "verano (vacaciones de verano en Bolivia)"
        contexto_estacion = "época de vacaciones largas, alta demanda de lectura recreativa"
    elif mes_actual in [3, 4, 5]:
        estacion          = "inicio de año escolar"
        contexto_estacion = "inicio de clases, alta demanda de libros académicos y de texto"
    elif mes_actual in [6, 7, 8]:
        estacion          = "mitad de año escolar"
        contexto_estacion = "mitad de año, posibles exámenes, demanda de libros de estudio"
    else:
        estacion          = "fin de año escolar"
        contexto_estacion = "fin de año, época de exámenes finales y trabajos de grado"

    # ── Prompt para Gemini ──
    prompt = f"""
    Eres un analista experto en gestión de bibliotecas. 
    Analiza los siguientes datos REALES del sistema y genera un informe 
    con observaciones inteligentes y sugerencias concretas de acción.

    ═══════════════════════════════════════
    📅 CONTEXTO TEMPORAL
    ═══════════════════════════════════════
    - Fecha actual: {datetime.now().strftime('%d/%m/%Y')}
    - Mes actual: {nombres_meses[mes_actual]} {anio_actual}
    - Estación/época: {estacion}
    - Contexto educativo: {contexto_estacion}

    ═══════════════════════════════════════
    📊 ESTADÍSTICAS GENERALES
    ═══════════════════════════════════════
    - Total de libros en catálogo: {total_libros}
    - Total de usuarios registrados: {total_usuarios}
    - Préstamos activos ahora mismo: {len(prestamos_activos)}
    - Préstamos devueltos (histórico): {len(prestamos_devueltos)}

    ═══════════════════════════════════════
    🏆 TOP 5 LIBROS MÁS PRESTADOS
    ═══════════════════════════════════════
{contexto_top_libros}

    ═══════════════════════════════════════
    📦 LIBROS CON STOCK CRÍTICO (≤2 unidades)
    ═══════════════════════════════════════
{contexto_stock_bajo}

    ═══════════════════════════════════════
    📅 PRÉSTAMOS POR MES
    ═══════════════════════════════════════
{contexto_prestamos_mes}

    ═══════════════════════════════════════
    📚 LIBROS POR CATEGORÍA
    ═══════════════════════════════════════
{contexto_categorias}

    ═══════════════════════════════════════
    👑 TOP 5 USUARIOS MÁS ACTIVOS
    ═══════════════════════════════════════
{contexto_top_usuarios}

    ═══════════════════════════════════════
    📝 INSTRUCCIONES DE ANÁLISIS
    ═══════════════════════════════════════
    Genera exactamente 5 puntos de análisis usando este formato HTML:

    <div class="insight">
        <span class="insight-icon">📈</span>
        <strong>Título del insight</strong>
        <p>Explicación detallada con datos concretos y sugerencia de acción.</p>
    </div>

    Los 5 puntos DEBEN cubrir:

    1. 📈 TENDENCIA DE PRÉSTAMOS: Analiza si los préstamos suben o bajan 
       comparando los meses. Detecta el mes pico y explica posible causa.

    2. 📦 ALERTA DE STOCK: Identifica los libros más prestados que tienen 
       poco stock. Si un libro fue prestado muchas veces pero tiene ≤3 unidades, 
       recomienda comprar más copias con urgencia. Sé específico: 
       "El libro X fue prestado N veces pero solo tiene M copias disponibles."

    3. 🗓️ SUGERENCIA ESTACIONAL: Basándote en que estamos en {estacion}, 
       recomienda qué tipo de libros debería promocionar o adquirir la biblioteca. 

    4. 🌟 CATEGORÍA ESTRELLA: Identifica la categoría más popular y sugiere 
       si se debería ampliar esa sección o si hay categorías descuidadas 
       que podrían potenciarse.

    5. 💡 PREDICCIÓN O ACCIÓN PRIORITARIA: Basándote en todos los datos, 
       da UNA predicción concreta sobre stock o demanda futura.

    IMPORTANTE:
    - Usa los datos reales, no inventes números.
    - Sé directo y accionable, no genérico.
    - Cada insight debe tener una sugerencia clara de QUÉ HACER.
    - Responde solo con los 5 divs HTML, sin texto adicional fuera de ellos.
    """

    try:
        respuesta = modelo.generate_content(prompt)
        return jsonify({'analisis': respuesta.text, 'estado': 'ok'})
    except Exception as e:
        print(f"Error análisis IA: {e}")
        return jsonify({'analisis': '<p>Error al generar análisis.</p>', 'estado': 'error'})