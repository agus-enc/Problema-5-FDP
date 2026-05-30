import struct
import os

# Constante Globales :
FORMATO = '<i30s24s16sB'
TAM_REGISTRO = struct.calcsize(FORMATO)  # Retorna exactamente 75 bytes

# Módulo 1 — Persistencia binaria de pacientes

# Función auxiliar para truncamiento seguro a nivel de bytes
def codificar_seguro(texto, max_bytes):
    bytes_codificados = texto.encode('utf-8')
    if len(bytes_codificados) <= max_bytes:
        return bytes_codificados
    # Trunca a nivel de byte, decodifica ignorando los caracteres rotos en el límite y vuelve a codificar
    return bytes_codificados[:max_bytes].decode('utf-8', errors='ignore').encode('utf-8')

def empaquetar_paciente(paciente):
    """
    Convierte un diccionario con los datos de un paciente en una cadena de bytes empaquetada según el formato binario.
    Precondición: 'paciente' debe ser un diccionario válido con las claves 'dni' (int), 'apellido' (str), 'nombre' (str), 'telefono' (str) y 'prioridad' (int).
    Postcondición: Retorna una secuencia de exactamente 75 bytes lista para ser escrita en disco, con sus campos de texto codificados en UTF-8 y truncados si exceden su límite.
    """
    dni = paciente['dni']

    apellido_bytes = codificar_seguro(paciente['apellido'], 30)
    nombre_bytes = codificar_seguro(paciente['nombre'], 24)
    telefono_bytes = codificar_seguro(paciente['telefono'], 16)
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
    Precondición: 'archivo' debe ser un descriptor de archivo abierto para lectura binaria ('rb'), y 'k' debe ser un entero no negativo.
    Postcondición: Retorna el diccionario del paciente correspondiente a la posición 'k', o devuelve None si el registro está fuera de rango o el archivo no existe.
    """
    # Se remueve la verificación de tipo y la apertura del archivo.
    # 'archivo' ahora es obligatoriamente un file object.
    archivo.seek(k * TAM_REGISTRO)
    registro_bytes = archivo.read(TAM_REGISTRO)

    if not registro_bytes or len(registro_bytes) < TAM_REGISTRO:
        return None

    return desempaquetar_paciente(registro_bytes)

# Módulo 2 — Índices en memoria

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
        # Lectura adelantada antes del bucle
        registro_bytes = archivo.read(TAM_REGISTRO)

        while registro_bytes and len(registro_bytes) == TAM_REGISTRO:
            paciente = desempaquetar_paciente(registro_bytes)
            dni = paciente['dni']
            apellido = paciente['apellido']

            indice_por_dni[dni] = k

            if apellido not in indice_por_apellido:
                indice_por_apellido[apellido] = []
            indice_por_apellido[apellido].append(k)

            k += 1
            registro_bytes = archivo.read(TAM_REGISTRO)

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

    if isinstance(archivo, str):
        with open(archivo, 'rb') as f:
            return leer_paciente(f, k)
    else:
        return leer_paciente(archivo, k)

# Módulo 3 — Reportes ordenados

# - Merge_sort del Problema 1 de la Semana adaptado al problema 5
def merge_sort(secuencia, key_funcion=lambda x: x):
    """
    Ordena una secuencia de elementos de forma no decreciente utilizando Merge Sort estable,
    soportando funciones de extracción de claves para registros complejos.

    Precondición:
        - 'secuencia' debe ser una estructura iterable (lista o tupla).
        - 'key_funcion' debe ser una función u objeto ejecutable que reciba un elemento
          de la secuencia y retorne una clave comparable. Por defecto es la función identidad.
    Postcondición:
        - Devuelve una nueva lista ordenada según el criterio provisto por 'key_funcion'.
        - Conserva el orden relativo original para claves idénticas (estabilidad garantizada).
        - La secuencia original de entrada permanece intacta.
    Complejidad:
        - Temporal: O(n log n)
        - Espacial: O(n) de espacio auxiliar.
    """
    n = len(secuencia)

    if n <= 1:
        return secuencia

    medio = n >> 1

    # Se propaga la función clave a las llamadas recursivas internas
    izq = merge_sort(secuencia[:medio], key_funcion)
    der = merge_sort(secuencia[medio:], key_funcion)

    return _privada_fusionar(izq, der, key_funcion)

def _privada_fusionar(izq, der, key_funcion=lambda x: x):
    """
    Combina dos sublistas ordenadas en una única lista ordenada de forma estable utilizando
    una función de extracción de claves de comparación.

    Precondición:
        - 'izq' y 'der' deben ser listas previamente ordenadas de forma no decreciente bajo la misma 'key_funcion'.
        - 'key_funcion' es una función de evaluación comparable válida.
    Postcondición:
        - Devuelve una nueva lista integrada y correctamente estabilizada bajo la clave evaluada.
    """
    resultado = []
    i = 0
    j = 0
    limite_izq = len(izq)
    limite_der = len(der)

    while i < limite_izq and j < limite_der:
        # Se evalúan las claves extraídas por la función en lugar de comparar los objetos directamente
        if key_funcion(izq[i]) <= key_funcion(der[j]):
            resultado.append(izq[i])
            i += 1
        else:
            resultado.append(der[j])
            j += 1

    resultado.extend(izq[i:])
    resultado.extend(der[j:])

    return resultado

# - Implementación de listar_pacientes_ordenados
def obtener_prioridad(paciente):
    """
    Extrae el valor del campo de prioridad para utilizarlo como clave de ordenamiento.

    Precondición:
        - 'paciente' debe ser un diccionario válido que contenga la clave 'prioridad' mapeada a un número entero.
    Postcondición:
        - Devuelve el valor entero correspondiente a la prioridad del paciente.
    """
    return paciente['prioridad']

def obtener_apellido(paciente):
    """
    Extrae y normaliza el campo de apellido para utilizarlo como clave de ordenamiento alfabético.

    Precondición:
        - 'paciente' debe ser un diccionario válido que contenga la clave 'apellido' mapeada a una cadena de caracteres.
    Postcondición:
        - Devuelve una cadena de texto con el apellido del paciente convertido a minúsculas.
    """
    return paciente['apellido'].lower()

def listar_pacientes_ordenados(ruta, criterio):
    """
    Lee todos los registros de pacientes del archivo binario y genera una lista ordenada.
    Precondición: 'ruta' apunta a un archivo binario existente y válido.
                  'criterio' debe ser una cadena con valor exacto "apellido" o "prioridad".
    Postcondición: Devuelve una lista de diccionarios de pacientes ordenados.
    """
    pacientes = []
    criterio = criterio.strip().lower()

    with open(ruta, 'rb') as archivo:
        registro = archivo.read(TAM_REGISTRO)

        while registro and len(registro) == TAM_REGISTRO:
            paciente = desempaquetar_paciente(registro)
            pacientes.append(paciente)
            registro = archivo.read(TAM_REGISTRO)

    if criterio == "apellido":
        return merge_sort(pacientes, obtener_apellido)

    if criterio == "prioridad":
        # Encadenamiento directo para las dos pasadas: preserva memoria al evitar alojar la lista parcial en variables
        return merge_sort(merge_sort(pacientes, obtener_apellido), obtener_prioridad)

    return pacientes

# Módulo 4 — Asignación de la agenda diaria por backtracking

def _explorar_asignacion(indice_paciente, asignacion_actual, franjas_ocupadas_actuales, pac_dia, franj, disp):
    """
    Explora recursivamente el árbol de estados para construir una asignación válida de turnos.
    Precondición:
        - 'indice_paciente' es un número entero válido dentro del rango de índices de 'pac_dia'.
        - 'asignacion_actual' es un diccionario con las asignaciones de pacientes consolidadas en la rama actual.
        - 'franjas_ocupadas_actuales' es un conjunto (set) con las franjas ya extraídas en la rama actual.
    Postcondición:
        - Devuelve True si logra construir un árbol completo válido hacia las hojas; False si se agotan las opciones sin éxito.
    Efectos secundarios:
        - Muta de manera controlada las estructuras 'asignacion_actual' y 'franjas_ocupadas_actuales' durante la exploración. Estos cambios se revierten garantizadamente por diseño (backtrack) si la rama explorada resulta infértil.
    """
    # Caso base
    if indice_paciente == len(pac_dia):
        return True

    paciente = pac_dia[indice_paciente]
    franjas_posibles = disp.get(paciente, [])

    for franja in franjas_posibles:
        if franja in franj and franja not in franjas_ocupadas_actuales:
            asignacion_actual[paciente] = franja
            franjas_ocupadas_actuales.add(franja)

            if _explorar_asignacion(indice_paciente + 1, asignacion_actual, franjas_ocupadas_actuales, pac_dia, franj,
                                    disp):
                return True

            del asignacion_actual[paciente]
            franjas_ocupadas_actuales.remove(franja)
    return False

def asignar_agenda(pacientes_del_dia, franjas, disponibilidad):
    """
    Asigna una franja horaria a cada paciente de la lista respetando su disponibilidad y la unicidad de las franjas.

    Precondición:
        - 'pacientes_del_dia' es una lista de identificadores de pacientes.
        - 'franjas' es una lista de horarios disponibles.
        - 'disponibilidad' es un diccionario {paciente: [franjas_posibles]}.
    Postcondición:
        - Devuelve un diccionario {paciente: franja} con una asignación válida, o None si no existe solución.
    """

    asignacion_inicial = {}
    franjas_ocupadas_inicial = set()
    franjas_set = set(franjas)
    if _explorar_asignacion(0, asignacion_inicial, franjas_ocupadas_inicial, pacientes_del_dia, franjas_set, disponibilidad):
        return asignacion_inicial
    return None

# -- SECCIÓN DE MENU --

def mostrar_opciones():
    """
    Imprime en la salida estándar la interfaz visual del menú principal del sistema.
    Precondición:
        - Ninguna.
    Postcondición:
        - Muestra el listado de las 5 opciones operativas disponibles.
    Efectos secundarios:
        - Modifica la salida estándar de la consola (stdout).
    """
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
    """
        Articula la ejecución global del sistema, inicializa los recursos físicos en disco y gestiona el bucle de interacción.
        Precondición:
            - El entorno de ejecución debe poseer permisos de lectura y escritura en el directorio de trabajo actual para poder montar 'pacientes.dat'.
        Postcondición:
            - Finaliza la ejecución del programa de manera controlada y segura al seleccionar la opción de salida.
        Efectos secundarios:
            - Crea y sobrescribe de manera destructiva el archivo binario inicial de pacientes en el disco local.
            - Modifica la salida estándar de la consola durante la interacción.
            - Suspende la ejecución esperando el ingreso de datos a través de la entrada estándar (stdin).
        """
    base_pacientes = "pacientes.dat"

    # === SOLUCIÓN DEL RUNTIME ERROR & CUMPLIMIENTO CONSIGNA I ===
    # 1. Crear el archivo con un set de datos iniciales de prueba
    if not os.path.exists(base_pacientes):
        pacientes_iniciales = [
            {'dni': 12345678, 'apellido': 'Perez', 'nombre': 'Juan', 'telefono': '11223344', 'prioridad': 2},
            {'dni': 87654321, 'apellido': 'Gomez', 'nombre': 'Maria', 'telefono': '55667788', 'prioridad': 1},
            {'dni': 45678912, 'apellido': 'Perez', 'nombre': 'Luis', 'telefono': '99001122', 'prioridad': 3}
        ]
        crear_archivo_pacientes(base_pacientes, pacientes_iniciales)

    # 2. Construir los índices en memoria RAM antes de iniciar el bucle interactivo
    indices_dni, indices_apellido = construir_indices(base_pacientes)

    ejecutando = True
    mostrar_opciones()

    while ejecutando:
        opcion = input("Seleccione una operación (1-5): ").strip()

        if opcion == "1":
            print("\n>>> MÓDULO DE BÚSQUEDA INDEXADA (O(1)) <<<")
            try:
                dni_objetivo = int(input("Ingrese el número de DNI a consultar: "))
                paciente_hallado = buscar_por_dni(base_pacientes, indices_dni, dni_objetivo)

                if paciente_hallado:
                    print(f"\n[Resultado] Paciente Encontrado:")
                    print(
                        f"DNI: {paciente_hallado['dni']} | {paciente_hallado['apellido']}, {paciente_hallado['nombre']} | Tel: {paciente_hallado['telefono']} | Prioridad: {paciente_hallado['prioridad']}")
                else:
                    print("\n[Resultado] El DNI ingresado no se encuentra en el sistema.")
            except ValueError:
                print("\n[Error] El DNI ingresado debe ser un número entero válido (evita puntos o letras).")

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
            franjas_base = ["08:00", "08:30", "09:00", "09:30"]

            print("\n--- Evaluando Caso 1: Asignación Posible ---")
            pacientes_caso1 = ["Juan", "Maria", "Pedro"]
            disp_caso1 = {"Juan": ["08:00", "08:30"], "Maria": ["08:00"], "Pedro": ["08:30", "09:00"]}
            resultado1 = asignar_agenda(pacientes_caso1, franjas_base, disp_caso1)

            if resultado1:
                for pac, fran in resultado1.items():
                    print(f"  - {pac} asignado a las {fran}")
            else:
                print("No se encontró solución.")

            print("\n--- Evaluando Caso 2: Sobre-restringido ---")
            pacientes_caso2 = ["Ana", "Luis", "Carlos"]
            disp_caso2 = {"Ana": ["09:00"], "Luis": ["09:00"], "Carlos": ["09:30"]}
            resultado2 = asignar_agenda(pacientes_caso2, franjas_base, disp_caso2)

            if resultado2:
                print("Asignación Exitosa (Inesperado).")
            else:
                print("Fallo esperado: No existe asignación válida posible debido a superposición.")

        elif opcion == "5":
            print("\n Programa finalizado. Gracias por utilizar el sistema de gestión médica. ")
            ejecutando = False

        else:
            print("\n[Error] Opción inválida. Ingrese un dígito del 1 al 5.")

# --- INTERFAZ DEL USUARIO ---
if __name__ == '__main__':
    menu_principal()