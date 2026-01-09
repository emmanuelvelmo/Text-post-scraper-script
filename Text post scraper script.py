from selenium import webdriver # Automatización de navegador web
from selenium.webdriver.chrome.service import Service # Gestión del servicio de Chrome
from selenium.webdriver.chrome.options import Options # Configuración de opciones del navegador
from selenium.webdriver.common.by import By # Localización de elementos web
import time # Funciones relacionadas con tiempo
import pathlib # Manejo moderno de rutas de archivos
import os # Funciones del sistema operativo

# VARIABLES GLOBALES
nombre_archivo_salida = "" # Nombre del archivo donde se guardarán los posts

# FUNCIONES
# Crea un archivo vacío para almacenar los posts
def crear_archivo_vacio(usuario):
    global nombre_archivo_salida
    
    nombre_archivo_salida = usuario + ".txt"
    
    ruta = pathlib.Path(nombre_archivo_salida) # Crear objeto Path con el nombre del archivo
    
    if ruta.exists(): # Verificar si el archivo ya existe
        os.remove(ruta) # Eliminar el archivo existente
    with open(ruta, 'w', encoding='utf-8'): # Crear nuevo archivo vacío
        pass

# Guarda un post individual en el archivo de salida
def guardar_post_individual(fecha, texto):
    with open(nombre_archivo_salida, 'a', encoding='utf-8') as archivo: # Abrir archivo en modo append
        archivo.write(fecha + "\n") # Escribir la fecha del post
        archivo.write(texto + "\n\n") # Escribir el texto del post con un salto de línea extra

# Extrae la fecha de un post y la formatea
def extraer_fecha_post(elemento_post):
    try:
        elemento_fecha = elemento_post.find_element(By.CSS_SELECTOR, 'time') # Buscar el elemento de tiempo
        fecha_iso = elemento_fecha.get_attribute('datetime') # Obtener el atributo datetime
        
        return f"{fecha_iso[8:10]}/{fecha_iso[5:7]}/{fecha_iso[0:4]}" # Formatear a DD/MM/AAAA
    except Exception:
        fecha_actual = time.localtime() # Obtener fecha actual si falla
        
        return f"{fecha_actual.tm_mday:02d}/{fecha_actual.tm_mon:02d}/{fecha_actual.tm_year}"

# Extrae el texto de un post
def extraer_texto_post(elemento_post):
    texto_completo = ""
    
    try:
        # Buscar el contenedor específico del texto del tweet
        elemento_texto = elemento_post.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
        
        # Obtener el texto directamente de ese contenedor
        texto_completo = elemento_texto.text.strip()
        
        # Limpiar espacios múltiples por si acaso
        texto_completo = ' '.join(texto_completo.split())
    except Exception:
        # Si no se encuentra el elemento (ej. en un post solo con imagen), se devuelve vacío
        pass
    
    return texto_completo

# Extrae todos los posts de la página actual
def extraer_posts_pagina(driver):
    posts = []
    try:
        elementos = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]') # Buscar todos los tweets
        
        for elemento in elementos:
            fecha = extraer_fecha_post(elemento) # Extraer fecha del post
            texto = extraer_texto_post(elemento) # Extraer texto del post
            
            if fecha and texto:
                posts.append((fecha, texto)) # Añadir post a la lista
    except Exception:
        pass
    
    return posts

# Desplaza la página hacia abajo para cargar más posts
def desplazar_pagina_cargar_posts(driver):
    altura_anterior = driver.execute_script("return document.body.scrollHeight") # Obtener altura actual
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Desplazar al final
    time.sleep(2) # Esperar a que cargue
    altura_nueva = driver.execute_script("return document.body.scrollHeight") # Obtener nueva altura
    
    return altura_nueva > altura_anterior # Retornar si la página creció

# Configura y devuelve una instancia de Chrome en modo headless
def configurar_navegador_chrome():
    opciones = Options()
    opciones.add_argument("--headless=new") # Ejecutar sin interfaz gráfica
    opciones.add_argument("--window-size=1280,720") # Tamaño de ventana
    opciones.add_argument("--disable-gpu") # Desactivar aceleración por hardware
    opciones.add_argument("--log-level=3") # Nivel de log mínimo
    opciones.add_argument("--no-sandbox") # Desactivar sandbox
    opciones.add_argument("--disable-dev-shm-usage") # Evitar problemas de memoria
    opciones.add_argument("--disable-extensions") # Desactivar extensiones
    opciones.add_argument("--disable-logging") # Desactivar logs
    opciones.add_argument("--silent") # Modo silencioso

    servicio = Service()

    try:
        return webdriver.Chrome(service=servicio, options=opciones) # Crear instancia de Chrome
    except Exception:
        return None

# Orquesta el proceso de extracción de posts para un usuario de X
def procesar_x(driver, usuario):
    url = f"https://x.com/{usuario}" # Construir URL del perfil
    print("0 posts...", end="\r") # Mostrar contador inicial

    crear_archivo_vacio(usuario) # Crear archivo de salida

    try:
        driver.get(url) # Navegar a la URL
        time.sleep(30) # Esperar a que cargue la página
    except Exception:
        print("") # Salto de línea si hay error
        
        return

    posts_guardados = [] # Lista para evitar duplicados
    contador = 0 # Contador de posts guardados
    intentos_scroll = 0 # Contador de intentos sin nuevos posts
    max_intentos_scroll = 5 # Límite de intentos

    while intentos_scroll < max_intentos_scroll:
        posts_actuales = extraer_posts_pagina(driver) # Extraer posts de la página
        nuevos = False

        for post in posts_actuales:
            if post not in posts_guardados: # Verificar si el post es nuevo
                posts_guardados.append(post) # Añadir a la lista de guardados
                fecha, texto = post
                guardar_post_individual(fecha, texto) # Guardar en archivo
                
                contador += 1
                nuevos = True
                
                print(f"{contador} posts...", end="\r") # Actualizar contador en pantalla

        if not desplazar_pagina_cargar_posts(driver): # Intentar cargar más posts
            intentos_scroll += 1 # Si no hay más, aumentar intentos
        else:
            intentos_scroll = 0 # Si hay nuevos, reiniciar contador

        time.sleep(1) # Pausa entre ciclos

    print("") # Salto de línea final

# BUCLE PRINCIPAL
while True:
    print("1. X (Twitter)")
    print("2. Facebook\n")

    opcion = input("Option: ").strip()
    if opcion != '1': # Solo se procesa la opción 1
        print("")
        
        continue

    usuario = input("Username: ").strip('"\'') # Obtener nombre de usuario
    if not usuario:
        print("")
        
        continue

    print("")
    
    driver = configurar_navegador_chrome() # Configurar navegador
    if not driver: # Si falla la configuración, reiniciar
    
        continue

    try:
        procesar_x(driver, usuario) # Iniciar proceso de extracción
    finally:
        driver.quit() # Asegurar cierre del navegador

    print("-" * 36 + "\n") # Separador
