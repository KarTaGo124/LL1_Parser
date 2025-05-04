import streamlit as st
from io import StringIO
import pandas as pd
from main import (
    leer_gramatica, obtener_simbolos, inicializar_gramatica,
    calcular_first, calcular_follow, construir_tabla_ll1,
    imprimir_tablas, imprimir_matriz_ll1, analizar_cadena
)

st.set_page_config(page_title="Parser LL(1)", layout="wide")

st.title("📘 Análisis Sintáctico LL(1)")
st.markdown("Sube una gramática y prueba tu cadena de entrada para ver el análisis paso a paso.")

# Subida de archivos
uploaded_grammar = st.file_uploader("📥 Sube tu archivo de gramática (`grammar.txt`)", type="txt")

# Entrada de cadena
input_string = st.text_input("✍️ Ingresa la cadena a analizar:", value="id + id")

if uploaded_grammar:
    reglas_raw = uploaded_grammar.read().decode("utf-8").splitlines()
    reglas = []
    for linea in reglas_raw:
        izq, der = linea.strip().split("->")
        izq = izq.strip()
        der = der.strip()
        if der == '#':
            reglas.append((izq, ['#']))
        else:
            reglas.append((izq, der.split()))

    variables, terminales = obtener_simbolos(reglas)
    inicio = reglas[0][0]
    grammar = inicializar_gramatica(variables, terminales, inicio)
    calcular_first(reglas, grammar)
    calcular_follow(reglas, grammar)
    tabla = construir_tabla_ll1(reglas, grammar, terminales)

    st.subheader("📊 Tablas FIRST y FOLLOW")
    data = []
    for simbolo, datos in grammar.items():
        if datos["tipo"] in ["V", "I"]:
            data.append({
                "Símbolo": simbolo,
                "Tipo": datos["tipo"],
                "FIRST": ", ".join(datos["first"]),
                "FOLLOW": ", ".join(datos["follow"])
            })
    st.dataframe(pd.DataFrame(data))

    st.subheader("🧮 Matriz LL(1) con recuperación (EXT / EXP)")
    matriz = {}
    columnas = sorted(set(terminales + ['$']))
    for nt in sorted(tabla.keys()):
        fila = {}
        for t in columnas:
            reglas_set = tabla[nt][t]
            if reglas_set:
                producciones = [f"{izq} → {' '.join(der)}" for izq, der in reglas_set]
                fila[t] = " / ".join(producciones)
            else:
                if t in grammar[nt]['follow'] or t == "$":
                    fila[t] = "EXT"
                elif t not in grammar[nt]['first'] and t not in grammar[nt]['follow']:
                    fila[t] = "EXP"
                else:
                    fila[t] = "-"
        matriz[nt] = fila
    df_matriz = pd.DataFrame(matriz).T
    st.dataframe(df_matriz)

    st.subheader("🔍 Análisis paso a paso")
    output_buffer = StringIO()
    import sys
    sys.stdout = output_buffer  # Redirigir salida estándar temporalmente
    analizar_cadena(input_string, tabla, grammar, inicio)
    sys.stdout = sys.__stdout__  # Restaurar salida estándar
    st.code(output_buffer.getvalue(), language='text')

else:
    st.info("⚠️ Esperando archivo de gramática...")

