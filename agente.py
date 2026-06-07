import os
import json
import subprocess
from groq import Groq
from dotenv import load_dotenv

# 1. Cargar clave del archivo .env
load_dotenv()

# 2. Inicializar cliente de Groq
client = Groq()

# --- HERRAMIENTA 1: ESCRIBIR ---
def escribir_archivo(nombre_archivo: str, contenido: str) -> str:
    """Crea o edita un archivo en la computadora con el contenido especificado."""
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        return f"Éxito: El archivo '{nombre_archivo}' fue creado/modificado correctamente."
    except Exception as e:
        return f"Error al escribir el archivo: {e}"

# --- HERRAMIENTA 2: LEER ---
def leer_archivo(nombre_archivo: str) -> str:
    """Lee el contenido de un archivo existente para revisar su código."""
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            return archivo.read()
    except Exception as e:
        return f"Error al leer el archivo '{nombre_archivo}': {e}"

# --- HERRAMIENTA 3: COMANDOS DE GIT/SISTEMA ---
def ejecutar_comando_sistema(comando: str) -> str:
    """Ejecuta comandos en la terminal (como git init, git add, git commit, git push)."""
    try:
        # Ejecuta el comando de forma segura en la carpeta actual
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, encoding="utf-8")
        if resultado.returncode == 0:
            return f"Éxito al ejecutar '{comando}':\n{resultado.stdout}"
        else:
            return f"Error al ejecutar '{comando}':\n{resultado.stderr}"
    except Exception as e:
        return f"Error inesperado del sistema: {e}"

def ejecutar_agente(instruccion_usuario):
    # Declaramos las tres herramientas para el modelo
    herramientas = [
        {
            "type": "function",
            "function": {
                "name": "escribir_archivo",
                "description": "Crea o modifica un archivo en el disco con el nombre y contenido indicados.",
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
                "description": "Lee y devuelve el contenido de un archivo existente en la carpeta.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre_archivo": {"type": "string"}
                    },
                    "required": ["nombre_archivo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ejecutar_comando_sistema",
                "description": "Ejecuta comandos de consola. Exclusivo para operaciones de Git como 'git init', 'git add .', 'git commit -m ...', o 'git push'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "comando": {"type": "string"}
                    },
                    "required": ["comando"]
                }
            }
        }
    ]

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": instruccion_usuario}],
        tools=herramientas,
        tool_choice="auto"
    )

    mensaje = respuesta.choices[0].message

    if mensaje.tool_calls:
        for llamada in mensaje.tool_calls:
            args = json.loads(llamada.function.arguments)
            
            if llamada.function.name == "escribir_archivo":
                print(f"\n[Agente]: Decidió CREAR/EDITAR '{args['nombre_archivo']}'")
                resultado = escribir_archivo(nombre_archivo=args['nombre_archivo'], contenido=args['contenido'])
                print(f"[Sistema]: {resultado}")
                
            elif llamada.function.name == "leer_archivo":
                print(f"\n[Agente]: Decidió LEER '{args['nombre_archivo']}'")
                print(f"[Sistema]: Archivo leído correctamente.")
                
            elif llamada.function.name == "ejecutar_comando_sistema":
                print(f"\n[Agente]: Decidió EJECUTAR COMANDO: {args['comando']}")
                resultado = ejecutar_comando_sistema(comando=args['comando'])
                print(f"[Sistema]: {resultado}")
    else:
        print(f"\nRespuesta del modelo: {mensaje.content}")

if __name__ == "__main__":
    print("--- AGENTE CODEX GIT-READY ACTIVO ---")
    print("Escribe tu instrucción (o 'salir' para terminar):")
    while True:
        usuario = input("\nTú: ")
        if usuario.lower() == 'salir':
            break
        ejecutar_agente(usuario)