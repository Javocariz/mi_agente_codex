import streamlit as st
import os
import json
from groq import Groq
from dotenv import load_dotenv
import subprocess

# Configuración visual avanzada
st.set_page_config(page_title="Codex Clone Agent", page_icon="⚡", layout="wide")
load_dotenv()

if "GROQ_API_KEY" in os.environ:
    client = Groq()
else:
    st.error("Falta la clave GROQ_API_KEY en tu archivo .env")
    st.stop()

# --- HERRAMIENTAS NATIVAS ---
def escribir_archivo(nombre_archivo: str, contenido: str) -> str:
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        return f"Éxito: El archivo '{nombre_archivo}' fue guardado/modificado."
    except Exception as e:
        return f"Error al escribir: {e}"

def leer_archivo(nombre_archivo: str) -> str:
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            return archivo.read()
    except Exception as e:
        return f"Error al leer '{nombre_archivo}': {e}"

def ejecutar_comando_sistema(comando: str) -> str:
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, encoding="utf-8")
        if resultado.returncode == 0:
            return f"Comando ejecutado con éxito (Exit code 0).\nSalida:\n{resultado.stdout}"
        else:
            return f"Error al ejecutar comando (Exit code {resultado.returncode}).\nDetalles:\n{resultado.stderr}"
    except Exception as e:
        return f"Error crítico: {e}"

# --- INTERFAZ DE USUARIO ---
st.title("⚡ Codex Clone - Entorno de Desarrollo Autónomo")

col_chat, col_preview = st.columns([1, 1])

# Inicializar memoria histórica con reglas de diseño estrictas
if "historial_codex" not in st.session_state:
    st.session_state.historial_codex = [
        {
            "role": "system", 
            "content": (
                "Eres un Agente de Ingeniería de Software avanzado estilo OpenAI Codex. "
                "Tienes acceso completo para leer, escribir archivos y ejecutar comandos.\n"
                "REGLAS DE DISEÑO Y CÓDIGO:\n"
                "1. ¡PROHIBIDO EL HTML PLANO SIN ESTILOS! Siempre que crees o edites una interfaz, agrégale un diseño CSS moderno, "
                "espectacular y limpio (usa paletas oscuras, fuentes sans-serif como Inter/Arial, bordes redondeados y sombras suaves).\n"
                "2. Edita los archivos directamente usando tus herramientas en lugar de solo dar explicaciones.\n"
                "3. Si un comando o la API fallan, corrige la sintaxis e intenta de nuevo de forma autónoma."
            )
        }
    ]

if "archivo_activo" not in st.session_state:
    st.session_state.archivo_activo = "index.html"

with col_preview:
    st.subheader("📁 Código Fuente en Vivo")
    
    lista_archivos = ["index.html", "estilos.css", "app.py"]
    if st.session_state.archivo_activo not in lista_archivos:
        lista_archivos.append(st.session_state.archivo_activo)
        
    idx_defecto = lista_archivos.index(st.session_state.archivo_activo)
    archivo_a_ver = st.selectbox("Archivo en edición actual:", lista_archivos, index=idx_defecto)
    st.session_state.archivo_activo = archivo_a_ver

    if os.path.exists(archivo_a_ver):
        with open(archivo_a_ver, "r", encoding="utf-8") as f:
            st.code(f.read(), language="html" if "html" in archivo_a_ver else "css" if "css" in archivo_a_ver else "python")
    else:
        st.info(f"El archivo '{archivo_a_ver}' se mostrará aquí cuando el agente lo cree.")
    
    st.markdown("---")
    st.subheader("🌐 Despliegue Directo")
    msg_commit = st.text_input("¿Qué cambios hiciste?", placeholder="Ej: Rediseño visual premium")
    if st.button("🚀 Empujar Cambios a GitHub Pages", use_container_width=True):
        if msg_commit:
            with st.spinner("Sincronizando repositorio remoto..."):
                subprocess.run("git add .", shell=True)
                subprocess.run(f'git commit -m "{msg_commit}"', shell=True)
                res = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
                st.success("¡Desplegado! Dale 30 segundos a GitHub para actualizar la URL.")
                st.balloons()
        else:
            st.warning("Escribe una descripción del avance.")

with col_chat:
    st.subheader("💬 Consola del Agente")
    
    # 🌟 MEJORA: Altura fija y scroll automático para los mensajes
    container_mensajes = st.container(height=500)
    
    with container_mensajes:
        for msg in st.session_state.historial_codex:
            if msg["role"] != "system" and "content" in msg and msg["content"]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

    # El chat input ahora se queda fijo abajo del contenedor gracias a la propiedad height
    if entrada_usuario := st.chat_input("Instrucción (ej: 'Rediseña la web con un estilo premium oscuro')"):
        st.session_state.historial_codex.append({"role": "user", "content": entrada_usuario})
        
        # Forzar repintado inmediato del mensaje del usuario
        with container_mensajes:
            with st.chat_message("user"):
                st.write(entrada_usuario)

        with container_mensajes:
            with st.chat_message("assistant"):
                contenedor_logs = st.empty()
                logs = []
                
                limite_pasos = 8
                paso_actual = 0
                
                herramientas = [
                    {
                        "type": "function",
                        "function": {
                            "name": "escribir_archivo",
                            "description": "Escribe o edita por completo un archivo en el disco.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "nombre_archivo": {"type": "string"},
                                    "contenido": {"type": "string"}
                                },
                                "required": ["nombre_archivo", "contenido"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "leer_archivo",
                            "description": "Lee el código de un archivo existente para comprenderlo.",
                            "parameters": {
                                "type": "object",
                                "properties": {"nombre_archivo": {"type": "string"}},
                                "required": ["nombre_archivo"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "ejecutar_comando_sistema",
                            "description": "Ejecuta comandos de consola para verificar el estado del proyecto.",
                            "parameters": {
                                "type": "object",
                                "properties": {"comando": {"type": "string"}},
                                "required": ["comando"]
                            }
                        }
                    }
                ]
                
                while paso_actual < limite_pasos:
                    paso_actual += 1
                    
                    try:
                        respuesta = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=st.session_state.historial_codex,
                            tools=herramientas,
                            tool_choice="auto"
                        )
                    except Exception as api_err:
                        logs.append(f"⚠️ Alerta API: Forzando reintento de formato...")
                        contenedor_logs.markdown("\n".join(logs))
                        st.session_state.historial_codex.append({
                            "role": "user",
                            "content": "ERROR DE CONEXIÓN: Por favor reintenta con un formato JSON plano y limpio."
                        })
                        continue
                    
                    mensaje_ia = respuesta.choices[0].message
                    
                    if not mensaje_ia.tool_calls:
                        st.write(mensaje_ia.content)
                        st.session_state.historial_codex.append({"role": "assistant", "content": mensaje_ia.content})
                        break
                    
                    dict_herramientas = []
                    for tool in mensaje_ia.tool_calls:
                        dict_herramientas.append({
                            "id": tool.id,
                            "type": "function",
                            "function": {
                                "name": tool.function.name,
                                "arguments": tool.function.arguments
                            }
                        })
                    
                    st.session_state.historial_codex.append({
                        "role": "assistant",
                        "content": mensaje_ia.content,
                        "tool_calls": dict_herramientas
                    })
                    
                    for tool in mensaje_ia.tool_calls:
                        nombre_func = tool.function.name
                        
                        try:
                            args = json.loads(tool.function.arguments)
                        except Exception:
                            st.session_state.historial_codex.append({
                                "role": "tool",
                                "tool_call_id": tool.id,
                                "name": nombre_func,
                                "content": "Error: Argumentos inválidos."
                            })
                            continue

                        if "nombre_archivo" in args:
                            st.session_state.archivo_activo = args["nombre_archivo"]

                        if nombre_func == "escribir_archivo":
                            logs.append(f"🛠️ Modificando `{args['nombre_archivo']}`...")
                            contenedor_logs.markdown("\n".join(logs))
                            resultado_ejecucion = escribir_archivo(args['nombre_archivo'], args['contenido'])
                            
                        elif nombre_func == "leer_archivo":
                            logs.append(f"📖 Leyendo `{args['nombre_archivo']}`...")
                            contenedor_logs.markdown("\n".join(logs))
                            resultado_ejecucion = leer_archivo(args['nombre_archivo'])
                            
                        elif nombre_func == "ejecutar_comando_sistema":
                            logs.append(f"💻 Ejecutando en consola: `{args['comando']}`...")
                            contenedor_logs.markdown("\n".join(logs))
                            resultado_ejecucion = ejecutar_comando_sistema(args['comando'])
                        
                        st.session_state.historial_codex.append({
                            "role": "tool",
                            "tool_call_id": tool.id,
                            "name": nombre_func,
                            "content": resultado_ejecucion
                        })
                
                st.rerun()