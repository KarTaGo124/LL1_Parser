# parser.py
from collections import defaultdict
import pandas as pd
from io import StringIO
import sys

EPSILON = 'ε'

# Utilidades

def reemplazar_epsilon(reglas):
    return [(izq, [EPSILON] if der == ['#'] else der) for izq, der in reglas]

def extraer_variables_terminales(reglas):
    variables = set()
    terminales = set()
    for izq, der in reglas:
        variables.add(izq)
        for simbolo in der:
            if simbolo.isupper():
                variables.add(simbolo)
            elif simbolo != EPSILON:
                terminales.add(simbolo)
    return sorted(variables), sorted(terminales)

def eliminar_recursion_izquierda(reglas):
    nuevas_reglas = []
    agrupadas = defaultdict(list)
    for izq, der in reglas:
        agrupadas[izq].append(der)

    for nt in list(agrupadas):
        directas = []
        indirectas = []
        for prod in agrupadas[nt]:
            if prod[0] == nt:
                directas.append(prod[1:])
            else:
                indirectas.append(prod)

        if directas:
            nuevo = nt + "'"
            for beta in indirectas:
                nuevas_reglas.append((nt, beta + [nuevo]))
            for alpha in directas:
                nuevas_reglas.append((nuevo, alpha + [nuevo]))
            nuevas_reglas.append((nuevo, [EPSILON]))
        else:
            for prod in agrupadas[nt]:
                nuevas_reglas.append((nt, prod))

    return nuevas_reglas

def factorizar_por_izquierda(reglas):
    agrupadas = defaultdict(list)
    for izq, der in reglas:
        agrupadas[izq].append(der)
    nuevas_reglas = []

    for nt in agrupadas:
        prefijos = defaultdict(list)
        for der in agrupadas[nt]:
            if der:
                prefijos[der[0]].append(der)

        for pref, prods in prefijos.items():
            if len(prods) > 1:
                nuevo = nt + "'"
                nuevas_reglas.append((nt, [pref, nuevo]))
                for prod in prods:
                    sufijo = prod[1:] if len(prod) > 1 else [EPSILON]
                    nuevas_reglas.append((nuevo, sufijo))
            else:
                nuevas_reglas.append((nt, prods[0]))

    return nuevas_reglas

def tiene_recursion_izquierda(reglas):
    for izq, der in reglas:
        if der and der[0] == izq:
            return True
    return False

def tiene_factorizacion_izquierda(reglas):
    agrupadas = defaultdict(list)
    for izq, der in reglas:
        agrupadas[izq].append(der)
    for prods in agrupadas.values():
        prefijos = [p[0] for p in prods if p]
        if len(set(prefijos)) < len(prefijos):
            return True
    return False

def es_ll1(reglas):
    return not tiene_recursion_izquierda(reglas) and not tiene_factorizacion_izquierda(reglas)

def inicializar_gramatica(variables, terminales, inicio):
    grammar = {}
    for v in variables:
        grammar[v] = {"tipo": "V", "first": [], "follow": []}
    grammar[inicio]["tipo"] = "I"
    for t in terminales:
        grammar[t] = {"tipo": "T", "first": [t]}
    grammar[inicio]["follow"] = ["$"]
    return grammar

def calcular_first(reglas, grammar):
    cambio = True
    while cambio:
        cambio = False
        for izq, der in reglas:
            if der == [EPSILON]:
                if EPSILON not in grammar[izq]['first']:
                    grammar[izq]['first'].append(EPSILON)
                    cambio = True
            else:
                for simbolo in der:
                    nuevos = [x for x in grammar[simbolo]['first'] if x != EPSILON]
                    if not set(nuevos).issubset(grammar[izq]['first']):
                        grammar[izq]['first'].extend(nuevos)
                        cambio = True
                    if EPSILON not in grammar[simbolo]['first']:
                        break
                else:
                    if EPSILON not in grammar[izq]['first']:
                        grammar[izq]['first'].append(EPSILON)
                        cambio = True

def calcular_follow(reglas, grammar):
    cambio = True
    while cambio:
        cambio = False
        for izq, der in reglas:
            for i in range(len(der)):
                simbolo = der[i]
                if simbolo in grammar and grammar[simbolo]['tipo'] in ['V', 'I']:
                    siguiente = der[i + 1:]
                    temp = []
                    for s in siguiente:
                        temp += [x for x in grammar[s]['first'] if x != EPSILON]
                        if EPSILON not in grammar[s]['first']:
                            break
                    else:
                        temp += grammar[izq]['follow']
                    if not set(temp).issubset(grammar[simbolo]['follow']):
                        grammar[simbolo]['follow'].extend(temp)
                        cambio = True

def construir_tabla_ll1(reglas, grammar, terminales):
    tabla = {v: {t: set() for t in terminales + ['$']} for v in grammar if grammar[v]['tipo'] in ['V', 'I']}
    for izq, der in reglas:
        first_alpha = []
        if der == [EPSILON]:
            for f in grammar[izq]['follow']:
                tabla[izq][f].add((izq, tuple(der)))
        else:
            for s in der:
                first_alpha += [x for x in grammar[s]['first'] if x != EPSILON]
                if EPSILON not in grammar[s]['first']:
                    break
            else:
                first_alpha.append(EPSILON)

            for t in first_alpha:
                if t != EPSILON:
                    tabla[izq][t].add((izq, tuple(der)))
            if EPSILON in first_alpha:
                for f in grammar[izq]['follow']:
                    tabla[izq][f].add((izq, tuple(der)))
    return tabla

def analizar_cadena(cadena, tabla, grammar, inicio):
    output = []
    cadena = cadena.strip().split() + ["$"]
    pila = ["$", inicio]

    while True:
        pila_str = ' '.join(pila)
        entrada_str = ' '.join(cadena)

        if pila == ["$"] and cadena == ["$"]:
            output.append((pila_str, entrada_str, "CADENA VÁLIDA"))
            break

        if not pila:
            output.append((pila_str, entrada_str, "Error: pila vacía"))
            output.append(("", "", "CADENA NO VÁLIDA"))
            break

        tope = pila[-1]
        simbolo = cadena[0]

        if grammar.get(tope, {}).get("tipo") in ["I", "V"]:
            reglas = list(tabla[tope].get(simbolo, []))
            if reglas:
                regla = reglas[0]
                pila.pop()
                if list(regla[1]) != ['#']:
                    pila += list(reversed(regla[1]))
                produccion_str = f"{regla[0]} → {' '.join(regla[1]) if list(regla[1]) != ['#'] else EPSILON}"
                output.append((' '.join(pila), ' '.join(cadena), f"Regla: {produccion_str}"))
            else:
                output.append((pila_str, entrada_str, f"Error: no hay regla para {tope} con '{simbolo}'"))
                output.append(("", "", "CADENA NO VÁLIDA"))
                break

        elif grammar.get(tope, {}).get("tipo") == "T":
            if tope == simbolo:
                pila.pop()
                cadena.pop(0)
                output.append((' '.join(pila), ' '.join(cadena), f"Match: {simbolo}"))
            else:
                output.append((pila_str, entrada_str, f"Error: se esperaba '{tope}' pero se encontró '{simbolo}'"))
                output.append(("", "", "CADENA NO VÁLIDA"))
                break

        else:
            output.append((pila_str, entrada_str, "Error: símbolo desconocido en pila"))
            output.append(("", "", "CADENA NO VÁLIDA"))
            break

    df = pd.DataFrame(output, columns=["Pila", "Entrada", "Acción"])
    return df
