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

