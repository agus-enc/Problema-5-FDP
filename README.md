## Informe

f) Justificar por escrito por qué la estabilidad del algoritmo de ordenamiento es relevante 
para el criterio "prioridad": describir el procedimiento de dos pasadas (ordenar por apellido y 
luego por prioridad) y explicar qué se rompería si el segundo ordenamiento no fuera estable. 

- Estabilidad
Un algoritmo de ordenamiento es estable si preserva el orden relativo de elementos con claves iguales, lo que importa cuando se ordena por múltiples criterios sucesivos. Esto implica que si dos registros A y B tienen la misma clave y A aparecía antes que B en la secuencia de entrada, tras aplicar el algoritmo, A obligatoriamente seguirá posicionándose antes que B. Esta propiedad esta garantizada en merge_sort gracias al uso de (<=) que garantiza la estabilidad, preservando el orden relativo original. 
- Procedimiento de dos pasadas
Para resolver un ordenamiento por múltiples criterios sucesivos, se debe aplica unas pasadas encadenadas en orden inverso de relevancia: la primera pasada posee el criterio secundario (desempate seleccionado) y en la segunda pasada se aplica el criterio principal con la base anterior.
- Quiebre de estabilidad
Si el algoritmo utilizado en la segunda pasada fuera inestable, el orden relativo de los elementos con claves iguales se volvería completamente impredecible. Los pacientes con una misma prioridad serían reubicados de manera caótica, destruyendo por completo el orden alfabético alcanzado en la primera pasada. Devolviendo bloques de prioridad cuyos apellidos internos quedarían desordenados y alterando el reporte final esperado.

h) Probar con un caso que tenga solución y con un caso sobre-restringido que no la tenga
(más pacientes que franjas compatibles). Para el caso con solución, verificar que la
asignación devuelta respeta todas las restricciones. Discutir: ¿cuántas asignaciones posibles
habría que revisar por fuerza bruta, y cuántas evita la poda?

Fuerza Bruta: Un enfoque ingenuo generaría todas las permutaciones de tamaño N (pacientes) sobre un conjunto de M (franjas). Matemáticamente, esto representa M!/(M−N)! asignaciones posibles. Si tuviéramos 10 franjas y 8 pacientes, la fuerza bruta generaría 1.814.400 configuraciones completas antes de validarlas individualmente contra el diccionario de disponibilidad.

Acción de la Poda: La poda altera radicalmente este crecimiento factorial. Al descartar la asignación de una franja ya ocupada e iterar únicamente sobre disponibilidad.get(paciente), el algoritmo corta de raíz las ramas que no llevarian a ningún lado del árbol de estados. En el Caso 2 probado en el código (Ana y Luis limitados ambos a las 09:00), la poda evita explorar todo sub-árbol derivado de asignarle a Ana cualquier otro horario, y falla rápido en el turno de Luis al detectar que el set de franjas_ocupadas ya contiene "09:00". No hay manera precisa de cuantificar cuantas asignaciones evita la poda, ya que depende del volumen de restricciones, pero reduce la complejidad real a una fracción ínfima de O(MN).