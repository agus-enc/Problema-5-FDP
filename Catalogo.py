import struct
import os

# Constante Globales :
FORMATO = '<i30s24s16sB'
TAM_REGISTRO = struct.calcsize(FORMATO)  # Retorna exactamente 75 bytes

# MODULO 1  Persistencia binaria de pacientes

def empaquetar_paciente(paciente):
    """
    Convierte un diccionario con los datos de un paciente en una cadena de bytes empaquetada según el formato binario.
    Precondición: 'paciente' debe ser un diccionario válido con las claves 'dni' (int), 'apellido' (str), 'nombre' (str), 'telefono' (str) y 'prioridad' (int).
    Postcondición: Retorna una secuencia de exactamente 75 bytes lista para ser escrita en disco, con sus campos de texto codificados en UTF-8 y truncados si exceden su límite.
    """
    dni = paciente['dni']                                               #Conversion de datos a binario con encode utf-8
    apellido_bytes = paciente['apellido'].encode('utf-8')[:30]
    nombre_bytes = paciente['nombre'].encode('utf-8')[:24]
    telefono_bytes = paciente['telefono'].encode('utf-8')[:16]
    prioridad = paciente['prioridad']
    
    return struct.pack(FORMATO, dni, apellido_bytes, nombre_bytes, telefono_bytes, prioridad)


def desempaquetar_paciente(registro_bytes):
    """
    Transforma un bloque de 75 bytes leídos del archivo binario en un diccionario de Python con los campos decodificados.
    Precondición: 'registro_bytes' debe ser una secuencia válida de exactamente 75 bytes estructurada bajo la constante FORMATO.
    Postcondición: Retorna un diccionario con los datos del paciente limpios de bytes de relleno (\x00) y con las cadenas de texto decodificadas a UTF-8.
    """
    valores = struct.unpack(FORMATO, registro_bytes)
    
    dni = valores[0]
    apellido = valores[1].rstrip(b'\x00').decode('utf-8', errors='ignore')
    nombre = valores[2].rstrip(b'\x00').decode('utf-8', errors='ignore')
    telefono = valores[3].rstrip(b'\x00').decode('utf-8', errors='ignore')
    prioridad = valores[4]
    
    return {
        'dni': dni,
        'apellido': apellido,
        'nombre': nombre,
        'telefono': telefono,
        'prioridad': prioridad
    }


def crear_archivo_pacientes(ruta, lista_pacientes):
    """
    Genera o sobrescribe un archivo binario en el disco escribiendo secuencialmente los registros de una lista de pacientes.
    Precondición: 'ruta' debe ser un string con un camino válido y 'lista_pacientes' debe ser una lista que contenga diccionarios estructurados de pacientes.
    Postcondición: Crea o reemplaza el archivo físico en la ruta indicada con un tamaño total equivalente a la cantidad de pacientes multiplicado por 75 bytes.
    """
    with open(ruta, 'wb') as archivo:
        for paciente in lista_pacientes:
            registro_bytes = empaquetar_paciente(paciente)
            archivo.write(registro_bytes)


def leer_paciente(archivo, k):
    """
    Lee y desempaqueta el paciente ubicado en la posición relativa indexada 'k' del archivo binario utilizando acceso directo.
    Precondición: 'archivo' debe ser una ruta (str) o un descriptor de archivo abierto para lectura binaria, y 'k' debe ser un entero no negativo.
    Postcondición: Retorna el diccionario del paciente correspondiente a la posición 'k', o devuelve None si el registro está fuera de rango o el archivo no existe.
    """
    if type(archivo) == str:
        with open(archivo, 'rb') as f:
            f.seek(k * TAM_REGISTRO)
            registro_bytes = f.read(TAM_REGISTRO)
    else:
        archivo.seek(k * TAM_REGISTRO)
        registro_bytes = archivo.read(TAM_REGISTRO)
        
    if not registro_bytes or len(registro_bytes) < TAM_REGISTRO:
        return None
        
    return desempaquetar_paciente(registro_bytes)


# MÓDULO 2 Indices en memoria

def construir_indices(ruta):
    """
    Escanea secuencialmente el archivo binario de pacientes una única vez para armar las tablas hash de búsqueda en la memoria ram.
    Precondición: 'ruta' debe ser un string que represente el camino hacia un archivo de pacientes binario existente o por crearse.
    Postcondición: Retorna una tupla con dos diccionarios: el índice único por DNI {dni: k} y el índice asociativo por apellido {apellido: [k1, k2...]}.
    """
    indice_por_dni = {}
    indice_por_apellido = {}
    
    if not os.path.exists(ruta):
        return indice_por_dni, indice_por_apellido

    with open(ruta, 'rb') as archivo:
        k = 0
        while True:
            registro_bytes = archivo.read(TAM_REGISTRO)
            if not registro_bytes or len(registro_bytes) < TAM_REGISTRO:
                break

            paciente = desempaquetar_paciente(registro_bytes)
            dni = paciente['dni']
            apellido = paciente['apellido']
            
            indice_por_dni[dni] = k
            
            if apellido not in indice_por_apellido:
                indice_por_apellido[apellido] = []
            indice_por_apellido[apellido].append(k)
            
            k += 1
            
    return indice_por_dni, indice_por_apellido


def buscar_por_dni(archivo, indice_por_dni, dni):
    """
    Encuentra y recupera los datos de un paciente a partir de su DNI en tiempo O(1) amortizado combinando el índice de memoria con acceso directo a disco.
    Precondición: 'archivo' debe ser una ruta o descriptor válido, 'indice_por_dni' debe ser el diccionario de índices cargado y 'dni' debe ser un entero.
    Postcondición: Retorna el diccionario del paciente hallado mediante un único salto posicional físico o None si el DNI no existe en el índice.
    
    [NOTA TEÓRICA MANDATORIA - PUNTO D]:
    - Con Índice (O(1) promedio): La localización de 'k' se resuelve en tiempo constante en la tabla hash en memoria. El acceso al archivo binario es directo con un único 'seek' sin importar el volumen total de datos.
    - Búsqueda Secuencial (O(n)): Sin índice, requiere obligatoriamente leer secuencialmente de disco hasta 'n' registros, degradando el rendimiento linealmente conforme crece el archivo.
    """
    if dni not in indice_por_dni:
        return None
        
    k = indice_por_dni[dni]
    
    if type(archivo) == str:
        with open(archivo, 'rb') as f:
            return leer_paciente(f, k)
    else:
        return leer_paciente(archivo, k)
    
# Modulo 3 Reportes ordenados 

# - Merge_sort del Problema 1 de la Semana
def merge_sort(secuencia, key_funcion):
    """
    Ordena una secuencia de forma no decreciente utilizando el algoritmo Merge Sort.
    Garantiza estabilidad en el ordenamiento de los registros.

    Precondición: 'secuencia' debe ser una lista iterable con datos homogéneos.
                  'key_funcion' es una función que extrae la clave de ordenación.
    Postcondición: Devuelve una nueva lista ordenada según el criterio de key_funcion.
                   La secuencia original no es modificada (Algoritmo no destructivo).
    Complejidad: O(n log n) en tiempo y O(n) en espacio auxiliar. 
    """
    lista_a_ordenar = list(secuencia)
    n = len(lista_a_ordenar)
    if n <= 1:
        resultado = lista_a_ordenar
    else:
        medio = n >> 1  
        
        izq = merge_sort(lista_a_ordenar[:medio], key_funcion)
        der = merge_sort(lista_a_ordenar[medio:], key_funcion)
        
        resultado = _privada_fusionar(izq, der, key_funcion)
    return resultado

def _privada_fusionar(izq, der, key_funcion):
    """
    Función auxiliar encargada de fusionar dos sublistas ordenadas de manera estable.
    """
    resultado = []
    i = 0
    j = 0
    limite_izq = len(izq)
    limite_der = len(der)
    while i < limite_izq and j < limite_der:
        if key_funcion(izq[i]) <= key_funcion(der[j]):
            resultado.append(izq[i])
            i += 1
        else:
            resultado.append(der[j])
            j += 1
    while i < limite_izq:
        resultado.append(izq[i])
        i += 1
    while j < limite_der:
        resultado.append(der[j])
        j += 1
    return resultado

# - Implementación de listar_pacientes_ordenados
def obtener_prioridad(paciente):
    """Retorna la prioridad de un paciente para el merge_sort."""
    return paciente['prioridad']

def obtener_apellido(paciente):
    """Retorna el apellido de un paciente en minúsculas."""
    return paciente['apellido'].lower()

def listar_pacientes_ordenados(ruta, criterio):
    """
    Lee todos los registros de pacientes del archivo binario y genera una lista ordenada.
    Precondición: 'ruta' apunta a un archivo binario existente y válido.
                  'criterio' debe ser una cadena con valor exacto "apellido" o "prioridad".
    Postcondición: Devuelve una lista de diccionarios de pacientes ordenados.
    """
    pacientes = []

    with open(ruta, 'rb') as archivo:
        registro = archivo.read(TAM_REGISTRO)
        
        while registro and len(registro) == TAM_REGISTRO: # Lectura secuencial de todo el archivo
            # Utiliazación de la función del módulo 1 para devolver el diccionario
            paciente = desempaquetar_paciente(registro) 
            
            pacientes.append(paciente)
            registro = archivo.read(TAM_REGISTRO)
 
    if criterio == "apellido":
        resultado = merge_sort(pacientes, obtener_apellido)
    
    elif criterio == "prioridad":
        # Primera Pasada: se ordena por el criterio de apellido 
        lista_ordenada_apellido = merge_sort(pacientes, obtener_apellido)
        # Segunda Pasada: se ordena usando el criterio de prioridad
        resultado = merge_sort(lista_ordenada_apellido, obtener_prioridad)
    else:
        resultado = pacientes

    return resultado

# -- SECCIÓN DE MENU --

def mostrar_opciones():
    """Imprime la interfaz visual del menú por consola."""
    print("\n" + "=" * 65)
    print("      SISTEMA DE GESTIÓN MÉDICA - CONTROL CENTRAL")
    print("=" * 65)
    print("1. Buscar registros de paciente por DNI")
    print("2. Generar reporte alfabético (por Apellido)")
    print("3. Generar reporte jerárquico (por Prioridad y Apellido)")
    print("4. Planificar asignación de agenda diaria (Backtracking)")
    print("5. Salir del sistema")
    print("=" * 65)

def menu_principal():
    base_pacientes = "pacientes.dat"
    ejecutando = True # Evitar utilizar break o un while true 

    mostrar_opciones() # Menu de inicio (fuera del loop para que no tape los resultados)

    while ejecutando:
        opcion = input("Seleccione una operación (1-5): ").strip()
        
        if opcion == "1":
            print("\n>>> MÓDULO DE BÚSQUEDA INDEXADA (O(1)) <<<")
            dni_objetivo = int(input("Ingrese el número de DNI a consultar: "))
            paciente_hallado = buscar_por_dni(base_pacientes, indices_dni, dni_objetivo)

            if paciente_hallado:
                print(f"\n[Resultado] Paciente Encontrado:")
                print(f"DNI: {paciente_hallado['dni']} | {paciente_hallado['apellido']}, {paciente_hallado['nombre']} | Tel: {paciente_hallado['telefono']} | Prioridad: {paciente_hallado['prioridad']}")
            else:
                print("\n[Resultado] El DNI ingresado no se encuentra en el sistema.")
            
        elif opcion == "2":
            print("\n>>> REPORTE DE PACIENTES ORDENADOS POR APELLIDO <<<")
            pacientes_ordenados = listar_pacientes_ordenados(base_pacientes, "apellido")   
            for p in pacientes_ordenados:
                print(f"DNI: {p['dni']} | {p['apellido']}, {p['nombre']} | Teléfono: {p['telefono']}")
                
        elif opcion == "3":
            print("\n>>> REPORTE DE PACIENTES POR PRIORIDAD (CON DESEMPATE ALFABÉTICO) <<<")
            pacientes_prioridad = listar_pacientes_ordenados(base_pacientes, "prioridad")
            for p in pacientes_prioridad:
                print(f"Prioridad: {p['prioridad']} | {p['apellido']}, {p['nombre']} | DNI: {p['dni']}")
                
        elif opcion == "4":
            print("\n>>> MÓDULO DE ASIGNACIÓN INTELIGENTE DE AGENDA (BACKTRACKING) <<<")
            # Módulo 4
            
        elif opcion == "5":
            print("\n Programa finalizado. Gracias por utilizar el sistema de gestión médica. ")
            ejecutando = False
            
        else:
            print("\n[Error] Opción inválida. Ingrese un dígito del 1 al 5.")

# --- INTERFAZ DEL USUARIO ---
menu_principal()