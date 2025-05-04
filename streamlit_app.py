import streamlit as st
import pandas as pd
from parser import (
    reemplazar_epsilon,
    extraer_variables_terminales,
    eliminar_recursion_izquierda,
    factorizar_por_izquierda,
    tiene_recursion_izquierda,
    tiene_factorizacion_izquierda,
    es_ll1,
    inicializar_gramatica,
    calcular_first,
    calcular_follow,
    construir_tabla_ll1,
    analizar_cadena
)

st.set_page_config(page_title="Analizador LL(1)", layout="wide")

st.title("🔍 Analizador Sintáctico LL(1)")
st.markdown("Sube tu gramática y analiza cadenas paso a paso. Las producciones con ε representan la cadena vacía.")

gram_input = st.text_area("📘 Gramática (una producción por línea, usar 'ε' para vacía):",
                           value="""E -> T E'
E' -> + T E' | ε
T -> F T'
T' -> * F T' | ε
F -> ( E ) | id""", height=200)
input_str = st.text_input("✍️ Cadena a analizar (tokens separados por espacio):", "id + id * id")

if st.button("Procesar Gramática"):
    reglas_raw = [line.strip() for line in gram_input.strip().splitlines() if line.strip()]
    reglas = []
    for linea in reglas_raw:
        izq, der = linea.split("->")
        izq = izq.strip()
        for alt in der.split("|"):
            prod = alt.strip().split()
            reglas.append((izq, prod if prod != ['ε'] else ['ε']))

    reglas = reemplazar_epsilon(reglas)

    if tiene_recursion_izquierda(reglas):
        reglas = eliminar_recursion_izquierda(reglas)
        st.warning("⚠️ Recursión por izquierda eliminada.")

    if tiene_factorizacion_izquierda(reglas):
        reglas = factorizar_por_izquierda(reglas)
        st.warning("⚠️ Gramática factorizada por izquierda.")

    variables, terminales = extraer_variables_terminales(reglas)
    inicio = reglas[0][0]
    grammar = inicializar_gramatica(variables, terminales, inicio)
    calcular_first(reglas, grammar)
    calcular_follow(reglas, grammar)
    tabla = construir_tabla_ll1(reglas, grammar, terminales)

    st.subheader("📊 Tabla de Símbolos")
    data = []
    for simbolo, info in grammar.items():
        if info['tipo'] in ['V', 'I']:
            data.append({
                "Símbolo": simbolo,
                "FIRST": ', '.join(info['first']),
                "FOLLOW": ', '.join(info['follow'])
            })
    st.dataframe(pd.DataFrame(data))

    st.subheader("📐 Tabla LL(1)")
    ll1_data = {nt: {} for nt in tabla}
    columnas = terminales + ['$']
    for nt in tabla:
        for t in columnas:
            reglas_set = tabla[nt][t]
            if reglas_set:
                reglas_str = ' | '.join(f"{izq} → {' '.join(der) if der != ('ε',) else 'ε'}" for izq, der in reglas_set)
                ll1_data[nt][t] = reglas_str
            else:
                if t in grammar[nt]['follow']:
                    ll1_data[nt][t] = 'EXT'
                else:
                    ll1_data[nt][t] = 'EXP'
    st.dataframe(pd.DataFrame(ll1_data).fillna("-").T)

    st.subheader("🧾 Análisis de la cadena")
    import io
    import sys

    # Redirigir stdout temporalmente para capturar la salida
    output = io.StringIO()
    sys.stdout = output
    analizar_cadena(input_str, tabla, grammar, inicio)
    sys.stdout = sys.__stdout__

    # Mostrar salida
    st.code(output.getvalue())
