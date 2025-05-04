# streamlit_app.py
import streamlit as st
import pandas as pd
from parser import (
    reemplazar_epsilon, extraer_variables_terminales, inicializar_gramatica,
    calcular_first, calcular_follow, construir_tabla_ll1,
    tiene_recursion_izquierda, tiene_factorizacion_izquierda,
    eliminar_recursion_izquierda, factorizar_por_izquierda,
    es_ll1, analizar_cadena
)

st.set_page_config(page_title="LL(1) Analyzer", layout="wide")

st.title("📘 Análisis Sintáctico LL(1) con Transformación Automática")
st.markdown("""
Ingresa una gramática en formato BNF. Separa producciones alternativas con `|` y usa `ε` (epsilon) para la cadena vacía.

**Ejemplo:**
```
E -> E + T | T
T -> T * F | F
F -> ( E ) | id
```
""")

gramatica_texto = st.text_area("✍️ Gramática:", height=200, value="""
E -> E + T | T
T -> T * F | F
F -> ( E ) | id
""")

cadena_input = st.text_input("🧪 Cadena a analizar (tokens separados por espacio):", "id + id * id")

if st.button("Analizar Gramática"):
    reglas_raw = [r.strip() for r in gramatica_texto.splitlines() if r.strip()]
    reglas = []
    for r in reglas_raw:
        if "->" not in r: continue
        izq, der = r.split("->")
        for prod in der.split("|"):
            reglas.append((izq.strip(), prod.strip().split()))

    reglas = reemplazar_epsilon(reglas)
    variables, terminales = extraer_variables_terminales(reglas)
    inicio = reglas[0][0]
    grammar = inicializar_gramatica(variables, terminales, inicio)
    calcular_first(reglas, grammar)
    calcular_follow(reglas, grammar)

    necesita_transformacion = not es_ll1(reglas)

    if necesita_transformacion:
        st.warning("La gramática no es LL(1). Aplicando transformaciones...")
        if tiene_recursion_izquierda(reglas):
            reglas = eliminar_recursion_izquierda(reglas)
        if tiene_factorizacion_izquierda(reglas):
            reglas = factorizar_por_izquierda(reglas)
        reglas = reemplazar_epsilon(reglas)
        variables, terminales = extraer_variables_terminales(reglas)
        grammar = inicializar_gramatica(variables, terminales, inicio)
        calcular_first(reglas, grammar)
        calcular_follow(reglas, grammar)
        st.success("Gramática transformada a LL(1).")
    else:
        st.success("La gramática es LL(1).")

    st.subheader("📑 Reglas resultantes")
    for izq, der in reglas:
        st.text(f"{izq} → {' '.join(der)}")

    st.subheader("📊 Tablas FIRST y FOLLOW")
    tabla = []
    for simbolo in variables:
        tabla.append({
            "Simbolo": simbolo,
            "FIRST": ", ".join(grammar[simbolo]["first"]),
            "FOLLOW": ", ".join(grammar[simbolo]["follow"])
        })
    st.dataframe(pd.DataFrame(tabla))

    st.subheader("📘 Tabla LL(1)")
    tabla_ll1 = construir_tabla_ll1(reglas, grammar, terminales)
    matriz = []
    columnas = terminales + ["$"]
    for nt in tabla_ll1:
        fila = {"NT": nt}
        for t in columnas:
            producciones = tabla_ll1[nt][t]
            if producciones:
                fila[t] = " / ".join([f"{izq} → {' '.join(der)}" for izq, der in producciones])
            else:
                first = set(grammar[nt]['first'])
                follow = set(grammar[nt]['follow'])
                if t in follow or t == "$":
                    fila[t] = "EXT"
                elif t not in first.union(follow):
                    fila[t] = "EXP"
                else:
                    fila[t] = ""
        matriz.append(fila)
    st.dataframe(pd.DataFrame(matriz).set_index("NT"))

    st.subheader("🔍 Análisis de cadena")
    pasos = analizar_cadena(cadena_input.strip(), tabla_ll1, grammar, inicio)
    df_pasos = pd.DataFrame(pasos)
    df_pasos = df_pasos.rename(columns={"pila": "📌 Pila", "entrada": "🎯 Entrada", "accion": "🔄 Acción"})
    st.dataframe(df_pasos, use_container_width=True)

    if pasos and pasos[-1]['accion'] == "CADENA VÁLIDA":
        st.success("✅ La cadena fue aceptada.")
    else:
        st.error("❌ La cadena fue rechazada.")
