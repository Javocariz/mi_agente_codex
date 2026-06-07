import streamlit as st
import os
import json
from groq import Groq
from dotenv import load_dotenv
import subprocess

# Configuración de la página web local
st.set_page_config(page_title="Agente Codex v2", page_icon="🤖", layout="wide")
load_dotenv()

# Inicializar cliente de Groq de forma segura
if "GROQ_API_KEY" in os.environ:
    client = Groq()
else:
    st.error("No se encontró la clave GROQ_API_KEY en tu archivo .env")
    st.stop()

# --- FUNCIONES / MÚSCULOS DEL AGENTE ---
def escribir_archivo(nombre_archivo: str, contenido: str) -> str:
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        return f"Éxito: Archivo '{nombre_archivo}' guardado."
    except Exception as e:
        return f"Error al escribir: {e}"

def leer_archivo(nombre_archivo: str) -> str:
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            return archivo.read()
    except Exception as e:
        return f"Error al leer '{nombre_archivo}': {e}"

def ejecutar_git(comando: str) -> str:
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, encoding="utf-8")
        if resultado.returncode == 0:
            return f"Éxito Git:\n{resultado.stdout}"
        else:
            return f"Alerta Git:\n{resultado.stderr}"
    except Exception as e:
        return f"Error de sistema: {e}"

# --- INTERFAZ VISUAL (UI) ---
st.title("🤖 Agente Codex - Espacio de Trabajo Inteligente")
st.caption("Modifica tu código en lenguaje natural y despliega a GitHub Pages al instante.")

# Crear dos columnas: Izquierda para el Chat, Derecha para Control de GitHub
col_chat, col_control = st.columns([2, 1])

with col_control:
    st.subheader("🌐 Sincronización con GitHub")
    st.info("Tu repositorio actual está conectado a GitHub.")
    
    # Botón mágico para que el usuario suba cambios con un clic
    mensaje_commit = st.text_input("Mensaje del avance:", placeholder="Ej: Agregé un botón moderno")
    
    if st.button("🚀 Subir Avances a GitHub Pages", use_container_width=True):
        if mensaje_commit:
            with st.spinner("Subiendo código..."):
                ejecutar_git("git add .")
                res_commit = ejecutar_git(f'git commit -m "{mensaje_commit}"')
                res_push = ejecutar_git("git push origin main")
                
                st.success("¡Avances subidos con éxito!")
                st.code(f"{res_commit}\n{res_push}")
                st.balloons()
        else:
            st.warning("Por favor escribe un mensaje para describir tus cambios antes de subir.")

with col_chat:
    st.subheader("💬 Habla con tu Agente")
    
    # Historial de chat en memoria de Streamlit para que no se borre al recargar
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar mensajes anteriores
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Entrada de texto del usuario estilo ChatGPT
    if prompt := st.chat_input("¿Qué cambio quieres hacer en tu página web?"):
        # Mostrar el mensaje del usuario en la pantalla
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Procesamiento del Agente
        with st.chat_message("assistant"):
            with st.spinner("El agente está trabajando en los archivos..."):
                # Formato de herramientas para Groq
                herramientas = [
                    {
                        "type": "function",
                        "function": {
                            "name": "escribir_archivo",
                            "description": "Crea o modifica un archivo en el disco.",
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
                            "description": "Lee el contenido de un archivo.",
                            "parameters": {
                                "type": "object",
                                "properties": {"nombre_archivo": {"type": "string"}},
                                "required": ["nombre_archivo"]
                            }
                        }
                    }
                ]

                # Llamar a la IA
                respuesta = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    tools=herramientas,
                    tool_choice="auto"
                )

                mensaje_ia = respuesta.choices[0].message
                
                # Ejecutar herramientas si la IA lo requiere
                if mensaje_ia.tool_calls:
                    for llamada in mensaje_ia.tool_calls:
                        args = json.loads(llamada.function.arguments)
                        if llamada.function.name == "escribir_archivo":
                            res = escribir_archivo(args['nombre_archivo'], args['contenido'])
                            st.success(f"🛠️ **Agente:** He modificado el archivo `{args['nombre_archivo']}` con éxito.")
                        elif llamada.function.name == "leer_archivo":
                            contenido = leer_archivo(args['nombre_archivo'])
                            st.info(f"📖 **Agente:** He leído el archivo `{args['nombre_archivo']}` para entender tu código.")
                    
                    st.write("¡Cambios aplicados localmente! Puedes revisarlos en tu barra lateral o probarlos subiéndolos a GitHub con el panel de la derecha.")
                    st.session_state.messages.append({"role": "assistant", "content": "Cambios aplicados en tus archivos locales."})
                else:
                    st.write(mensaje_ia.content)
                    st.session_state.messages.append({"role": "assistant", "content": mensaje_ia.content})