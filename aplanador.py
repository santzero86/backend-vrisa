import os

def aplanar_proyecto(ruta_proyecto, archivo_salida="proyecto_aplanado.txt"):
    """
    Recorre un directorio de proyecto y guarda la estructura y el contenido
    de los archivos en un único archivo de texto.

    :param ruta_proyecto: La ruta al directorio raíz del proyecto.
    :param archivo_salida: El nombre del archivo donde se guardará el resultado.
    """

    # --- Configuración de Exclusiones ---
    # Agrega aquí los nombres de directorios que quieres ignorar.
    directorios_ignorados = {
        'node_modules',
        'vrisa_env',
        'venv',
        'env',
        '.git',
        '__pycache__',
        'migrations',
        'media',
        'static_root',
        '.vscode',
        '.idea',
    }

    # Agrega aquí las extensiones de archivo que quieres ignorar.
    extensiones_ignoradas = {
        '.pyc',
        '.log',
        '.sqlite3',
        '.db',
        '.DS_Store',
        '.env',
        '.svg',
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
    }
    
    # Agrega aquí nombres de archivos específicos a ignorar.
    archivos_ignorados = {
        'manage.py', # Generalmente no es necesario para entender la lógica principal
        archivo_salida # Para no incluir el propio archivo de salida
    }

    try:
        with open(archivo_salida, "w", encoding="utf-8") as salida:
            salida.write(f"Estructura y contenido del proyecto en: {os.path.abspath(ruta_proyecto)}\n")
            salida.write("=" * 80 + "\n\n")

            for ruta_actual, dirs, files in os.walk(ruta_proyecto):
                # Ignorar directorios no deseados
                dirs[:] = [d for d in dirs if d not in directorios_ignorados]

                # Obtener la ruta relativa para una mejor visualización
                ruta_relativa = os.path.relpath(ruta_actual, ruta_proyecto)
                if ruta_relativa == ".":
                    ruta_relativa = "" # Para el directorio raíz

                # Escribir la estructura del directorio
                nivel_profundidad = ruta_relativa.count(os.sep)
                prefijo = "    " * nivel_profundidad
                if ruta_relativa:
                    salida.write(f"{prefijo}[{os.path.basename(ruta_actual)}/]\n")

                # Procesar archivos en el directorio actual
                for nombre_archivo in sorted(files):
                    # Comprobar si el archivo debe ser ignorado
                    if nombre_archivo in archivos_ignorados:
                        continue
                    if os.path.splitext(nombre_archivo)[1].lower() in extensiones_ignoradas:
                        continue

                    # Escribir el nombre del archivo
                    salida.write(f"{prefijo}    - {nombre_archivo}\n")
                    
                    try:
                        ruta_completa_archivo = os.path.join(ruta_actual, nombre_archivo)
                        
                        # Escribir la cabecera del contenido del archivo
                        salida.write("-" * 80 + "\n")
                        salida.write(f"// Ruta del archivo: {os.path.join(ruta_relativa, nombre_archivo).replace(os.sep, '/')}\n")
                        salida.write("-" * 80 + "\n")
                        
                        # Leer y escribir el contenido del archivo
                        with open(ruta_completa_archivo, "r", encoding="utf-8", errors="ignore") as archivo:
                            contenido = archivo.read()
                            salida.write(contenido)
                        
                        salida.write("\n\n" + "=" * 80 + "\n\n")

                    except Exception as e:
                        salida.write(f"// No se pudo leer el archivo: {nombre_archivo}. Error: {e}\n\n")
        
        print(f"¡Éxito! El proyecto ha sido aplanado en el archivo: {archivo_salida}")

    except Exception as e:
        print(f"Ocurrió un error al generar el archivo: {e}")


if __name__ == "__main__":
    # La ruta del proyecto es el directorio actual donde se ejecuta el script.
    ruta_del_proyecto = os.getcwd() 
    
    # Llama a la función para aplanar el proyecto.
    aplanar_proyecto(ruta_del_proyecto)