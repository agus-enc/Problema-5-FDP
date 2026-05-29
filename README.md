
i) Justificar por escrito por qué la estabilidad del algoritmo de ordenamiento es relevante 
para el criterio "prioridad": describir el procedimiento de dos pasadas (ordenar por apellido y 
luego por prioridad) y explicar qué se rompería si el segundo ordenamiento no fuera estable. 

- Estabilidad
Un algoritmo de ordenamiento es estable si preserva el orden relativo de elementos con claves iguales, lo que importa cuando se ordena por múltiples criterios sucesivos. Esto implica que si dos registros A y B tienen la misma clave y A aparecía antes que B en la secuencia de entrada, tras aplicar el algoritmo, A obligatoriamente seguirá posicionándose antes que B. Esta propiedad esta garantizada en merge_sort gracias al uso de (<=) que garantiza la estabilidad, preservando el orden relativo original. 
- Procedimiento de dos pasadas
Para resolver un ordenamiento por múltiples criterios sucesivos, se debe aplica unas pasadas encadenadas en orden inverso de relevancia: la primera pasada posee el criterio secundario (desempate seleccionado) y en la segunda pasada se aplica el criterio principal con la base anterior.
- Quiebre de estabilidad
Si el algoritmo utilizado en la segunda pasada fuera inestable, el orden relativo de los elementos con claves iguales se volvería completamente impredecible. Los pacientes con una misma prioridad serían reubicados de manera caótica, destruyendo por completo el orden alfabético alcanzado en la primera pasada. Devolviendo bloques de prioridad cuyos apellidos internos quedarían desordenados y alterando el reporte final esperado.  