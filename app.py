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
    """Ejecuta un comando en la terminal local y devuelve el resultado (STDOUT o STDERR)."""
    try:
        # Ejecución segura capturando las salidas de texto
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, encoding="utf-8")
        if resultado.returncode == 0:
            return f"Comando ejecutado con éxito (Exit code 0).\nSalida de la terminal:\n{resultado.stdout}"
        else:
            return f"Error al ejecutar comando (Exit code {resultado.returncode}).\nDetalles del error:\n{resultado.stderr}"
    except Exception as e:
        return f"Error crítico del sistema al intentar ejecutar el comando: {e}"

# --- INTERFAZ DE USUARIO ---
st.title("⚡ Codex Clone - Entorno de Desarrollo Autónomo")

col_chat, col_preview = st.columns([1, 1])

# Inicializar memoria histórica con instrucciones de comportamiento estrictas (Prompt del Sistema)
if "historial_codex" not in st.session_state:
    st.session_state.historial_codex = [
        {
            "role": "system", 
            "content": (
                "Eres un Agente de Ingeniería de Software avanzado estilo OpenAI Codex. "
                "Tienes acceso completo para leer, escribir archivos y ejecutar comandos del sistema. "
                "REGLAS ESTRICTAS:\n"
                "1. No expliques cómo programar, edita los archivos directamente usando tus herramientas.\n"
                "2. Cada vez que crees o modifiques un archivo, utiliza la herramienta 'ejecutar_comando_sistema' "
                "para verificar el entorno o comprobar que no rompiste la estructura.\n"
                "3. Si una herramienta o comando te devuelve un error, analiza detalladamente el fallo, "
                "corrige el código en el archivo correspondiente y vuelve a probar. No te rindas hasta que todo funcione perfectamente."
            )
        }
    ]

with col_preview:
    st.subheader("📁 Código Fuente en Vivo")
    archivo_a_ver = st.selectbox("Selecciona un archivo para inspeccionar:", ["index.html", "estilos.css", "app.py"])
    if os.path.exists(archivo_a_ver):
        with open(archivo_a_ver, "r", encoding="utf-8") as f:
            st.code(f.read(), language="html" if "html" in archivo_a_ver else "css" if "css" in archivo_a_ver else "python")
    else:
        st.info(f"El archivo '{archivo_a_ver}' se mostrará aquí cuando el agente lo cree.")
    
    st.markdown("---")
    st.subheader("🌐 Despliegue Directo")
    msg_commit = st.text_input("¿Qué cambios hiciste?", placeholder="Ej: Rediseño completo de la UI")
    if st.button("🚀 Empujar Cambios a GitHub Pages", use_container_width=True):
        if msg_commit:
            with st.spinner("Sincronizando repositorio remoto..."):
                subprocess.run("git add .", shell=True)
                subprocess.run(f'git commit -m "{msg_commit}"', shell=True)
                res = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
                st.success("¡Desplegado con éxito!")
                st.balloons()
        else:
            st.warning("Escribe una descripción del avance.")

with col_chat:
    st.subheader("💬 Consola del Agente")
    
    # Mostrar el historial de forma segura
    for msg in st.session_state.historial_codex:
        if msg["role"] != "system" and "content" in msg and msg["content"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if entrada_usuario := st.chat_input("¿Qué módulo o mejora quieres agregar a tu web?"):
        st.session_state.historial_codex.append({"role": "user", "content": entrada_usuario})
        with st.chat_message("user"):
            st.write(entrada_usuario)

        with st.chat_message("assistant"):
            contenedor_logs = st.empty()
            logs = []
            
            # Subimos el límite de pasos a 7 para permitirle escribir, probar y autocorregirse si falla
            limite_pasos = 7
            paso_actual = 0
            
            # Definición de la caja de herramientas con la nueva función de terminal
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
                        "description": "Ejecuta comandos de consola en la terminal de la computadora (como 'dir', 'git status', etc.) para verificar el estado del proyecto.",
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
                
                respuesta = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.historial_codex,
                    tools=herramientas,
                    tool_choice="auto"
                )
                
                mensaje_ia = respuesta.choices[0].message
                
                # Si el agente decide que ya terminó y no invoca más herramientas
                if not mensaje_ia.tool_calls:
                    st.write(mensaje_ia.content)
                    st.session_state.historial_codex.append({"role": "assistant", "content": mensaje_ia.content})
                    break
                
                # Convertir la llamada en un formato de diccionario compatible para la memoria
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
                
                # Ejecutar herramientas dinámicamente
                for tool in mensaje_ia.tool_calls:
                    nombre_func = tool.function.name
                    args = json.loads(tool.function.arguments)
                    
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
                    
                    # Inyectar el feedback del sistema directo a la mente del modelo
                    st.session_state.historial_codex.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "name": nombre_func,
                        "content": resultado_ejecucion
                    })
            
            st.rerun()