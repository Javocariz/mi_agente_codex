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
            return f"Comando ejecutado con éxito (Exit code 0).\nSalida de la terminal:\n{resultado.stdout}"
        else:
            return f"Error al ejecutar comando (Exit code {resultado.returncode}).\nDetalles del error:\n{resultado.stderr}"
    except Exception as e:
        return f"Error crítico del sistema al intentar ejecutar el comando: {e}"

# --- INTERFAZ DE USUARIO ---
st.title("⚡ Codex Clone - Entorno de Desarrollo Autónomo")

col_chat, col_preview = st.columns([1, 1])

# Inicializar memoria histórica y tracking del archivo activo
if "historial_codex" not in st.session_state:
    st.session_state.historial_codex = [
        {
            "role": "system", 
            "content": (
                "Eres un Agente de Ingeniería de Software avanzado estilo OpenAI Codex. "
                "Tienes acceso completo para leer, escribir archivos y ejecutar comandos del sistema.\n"
                "REGLAS ESTRICTAS:\n"
                "1. No expliques cómo programar, edita los archivos directamente usando tus herramientas.\n"
                "2. Cada vez que crees o modifiques un archivo, utiliza la herramienta 'ejecutar_comando_sistema' "
                "para verificar el entorno o comprobar que no rompiste la estructura.\n"
                "3. Si la API genera un error de formato (BadRequestError) o un comando falla, ajusta tu sintaxis e intenta de nuevo."
            )
        }
    ]

if "archivo_activo" not in st.session_state:
    st.session_state.archivo_activo = "index.html"

with col_preview:
    st.subheader("📁 Código Fuente en Vivo")
    
    # El selector ahora lee y se sincroniza con el estado interno del agente
    lista_archivos = ["index.html", "estilos.css", "app.py"]
    if st.session_state.archivo_activo not in lista_archivos:
        lista_archivos.append(st.session_state.archivo_activo)
        
    idx_defecto = lista_archivos.index(st.session_state.archivo_activo)
    archivo_a_ver = st.selectbox("Archivo en edición actual:", lista_archivos, index=idx_defecto)
    
    # Guardar la selección manual del usuario por si quiere cambiar de pestaña
    st.session_state.archivo_activo = archivo_a_ver

    if os.path.exists(archivo_a_ver):
        with open(archivo_a_ver, "r", encoding="utf-8") as f:
            st.code(f.read(), language="html" if "html" in archivo_a_ver else "css" if "css" in archivo_a_ver else "python")
    else:
        st.info(f"El archivo '{archivo_a_ver}' se mostrará aquí cuando el agente lo cree.")
    
    st.markdown("---")
    st.subheader("🌐 Despliegue Directo")
    msg_commit = st.text_input("¿Qué cambios hiciste?", placeholder="Ej: Seccion de comentarios operativa")
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
    
    for msg in st.session_state.historial_codex:
        if msg["role"] != "system" and "content" in msg and msg["content"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if entrada_usuario := st.chat_input("¿Qué módulo o diseño quieres agregar ahora?"):
        st.session_state.historial_codex.append({"role": "user", "content": entrada_usuario})
        with st.chat_message("user"):
            st.write(entrada_usuario)

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
                        "description": "Ejecuta comandos de consola en la terminal de la computadora para verificar el estado del proyecto.",
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
                    logs.append(f"⚠️ Alerta: Error de formato del modelo. Solicitando reintento...")
                    contenedor_logs.markdown("\n".join(logs))
                    st.session_state.historial_codex.append({
                        "role": "user",
                        "content": "ERROR DE CONEXIÓN: Tu llamada de función anterior falló. Por favor reintenta con un formato JSON plano y limpio."
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

                    # Sincronizar dinámicamente el visor con el archivo que se está modificando o leyendo
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