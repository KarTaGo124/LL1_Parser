import re
import json

# Leer gramática desde archivo
def leer_gramatica(archivo):
    with open(archivo, "r") as f:
        reglas_raw = f.readlines()
    reglas = []
    for linea in reglas_raw:
        izq, der = linea.strip().split("->")
        izq = izq.strip()
        der = der.strip()
        if der == '#':
            reglas.append((izq, ['#']))
        else:
            reglas.append((izq, der.split()))
    return reglas


# Extraer símbolos
def obtener_simbolos(reglas):
    variables = set()
    terminales = set()
    for izq, der in reglas:
        variables.add(izq)
        for simbolo in der:
            if not simbolo.isupper() and simbolo != '#':
                terminales.add(simbolo)
            elif simbolo.isupper() and simbolo != izq:
                variables.add(simbolo)
    return list(variables), list(terminales)


# Inicializar estructura de símbolos
def inicializar_gramatica(variables, terminales, inicio):
    grammar = {}
    for v in variables:
        grammar[v] = {"tipo": "V", "first": [], "follow": []}
    grammar[inicio]["tipo"] = "I"
    for t in terminales:
        grammar[t] = {"tipo": "T", "first": [t]}
    grammar[inicio]["follow"] = ["$"]
    return grammar


# Calcular FIRST
def calcular_first(reglas, grammar):
    cambio = True
    while cambio:
        cambio = False
        for izq, der in reglas:
            if der == ['#']:
                if '#' not in grammar[izq]['first']:
                    grammar[izq]['first'].append('#')
                    cambio = True
            else:
                for simbolo in der:
                    nuevos = [x for x in grammar[simbolo]['first'] if x != '#']
                    if not set(nuevos).issubset(grammar[izq]['first']):
                        grammar[izq]['first'].extend(nuevos)
                        cambio = True
                    if '#' not in grammar[simbolo]['first']:
                        break
                else:
                    if '#' not in grammar[izq]['first']:
                        grammar[izq]['first'].append('#')
                        cambio = True


# Calcular FOLLOW
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
                        temp += [x for x in grammar[s]['first'] if x != '#']
                        if '#' not in grammar[s]['first']:
                            break
                    else:
                        temp += grammar[izq]['follow']
                    if not set(temp).issubset(grammar[simbolo]['follow']):
                        grammar[simbolo]['follow'].extend(temp)
                        cambio = True


# Construir tabla LL(1)
def construir_tabla_ll1(reglas, grammar, terminales):
    tabla = {v: {t: set() for t in terminales + ['$']} for v in grammar if grammar[v]['tipo'] in ['V', 'I']}
    for izq, der in reglas:
        first_alpha = []
        if der == ['#']:
            for f in grammar[izq]['follow']:
                tabla[izq][f].add((izq, tuple(der)))
        else:
            for s in der:
                first_alpha += [x for x in grammar[s]['first'] if x != '#']
                if '#' not in grammar[s]['first']:
                    break
            else:
                first_alpha.append('#')

            for t in first_alpha:
                if t != '#':
                    tabla[izq][t].add((izq, tuple(der)))
            if '#' in first_alpha:
                for f in grammar[izq]['follow']:
                    tabla[izq][f].add((izq, tuple(der)))
    return tabla


# Imprimir tabla con EXT/EXP
def imprimir_matriz_ll1(tabla, terminales, grammar):
    print("\n\nMATRIZ LL(1) [con recuperación: EXT / EXP]\n")
    terminales = sorted(set(terminales + ['$']))

    header = f"{'':<15}" + "".join(f"{t:<25}" for t in terminales)
    print(header)
    print("-" * len(header))

    for nt in sorted(tabla.keys()):
        fila = f"{nt:<15}"
        for t in terminales:
            reglas = tabla[nt][t]
            if reglas:
                producciones = [f"{izq} → {' '.join(der)}" for izq, der in sorted(reglas)]
                fila += f"{' / '.join(producciones):<25}"
            else:
                first = set(grammar[nt]['first'])
                follow = set(grammar[nt]['follow'])
                if t in follow or t == "$":
                    fila += f"{'EXT':<25}"
                elif t not in first.union(follow) and t != "$":
                    fila += f"{'EXP':<25}"
                else:
                    fila += f"{'-':<25}"
        print(fila)


# Imprimir FIRST y FOLLOW
def imprimir_tablas(grammar):
    print("\nTABLAS FIRST y FOLLOW")
    print(f"{'Símbolo':<10} {'Tipo':<8} {'FIRST':<20} {'FOLLOW':<20}")
    print("-" * 60)
    for simbolo, datos in grammar.items():
        tipo = datos['tipo']
        first = ", ".join(sorted(set(datos.get('first', []))))
        follow = ", ".join(sorted(set(datos.get('follow', [])))) if 'follow' in datos else "-"
        print(f"{simbolo:<10} {tipo:<8} {first:<20} {follow:<20}")


# Analizar una cadena
def analizar_cadena(cadena, tabla, grammar, inicio):
    print("\nANÁLISIS LL(1) - Traza paso a paso")
    print(f"{'Stack':<30} {'Input':<30} {'Acción'}")
    print("-" * 90)

    cadena = cadena.strip().split() + ["$"]
    pila = ["$", inicio]

    while True:
        pila_str = ' '.join(pila)
        entrada_str = ' '.join(cadena)

        if pila == ["$"] and cadena == ["$"]:
            print(f"{pila_str:<30} {entrada_str:<30} CADENA VÁLIDA")
            break

        if not pila:
            print(f"{pila_str:<30} {entrada_str:<30} Error: pila vacía")
            print("CADENA NO VÁLIDA")
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
                produccion_str = f"{regla[0]} → {' '.join(regla[1]) if list(regla[1]) != ['#'] else 'ε'}"
                print(f"{' '.join(pila):<30} {' '.join(cadena):<30} Regla: {produccion_str}")
            else:
                print(f"{pila_str:<30} {entrada_str:<30} Error: no hay regla para {tope} con '{simbolo}'")
                print("CADENA NO VÁLIDA")
                break

        elif grammar.get(tope, {}).get("tipo") == "T":
            if tope == simbolo:
                pila.pop()
                cadena.pop(0)
                print(f"{' '.join(pila):<30} {' '.join(cadena):<30} Match: {simbolo}")
            else:
                print(f"{pila_str:<30} {entrada_str:<30} Error: se esperaba '{tope}' pero se encontró '{simbolo}'")
                print("CADENA NO VÁLIDA")
                break

        else:
            print(f"{pila_str:<30} {entrada_str:<30} Error: símbolo desconocido en pila")
            print("CADENA NO VÁLIDA")
            break



# main(){}
reglas = leer_gramatica("grammar.txt")
variables, terminales = obtener_simbolos(reglas)
inicio = reglas[0][0]
grammar = inicializar_gramatica(variables, terminales, inicio)
calcular_first(reglas, grammar)
calcular_follow(reglas, grammar)
tabla = construir_tabla_ll1(reglas, grammar, terminales)

imprimir_tablas(grammar)
imprimir_matriz_ll1(tabla, terminales, grammar)

with open("input.txt", "r") as f:
    entrada = f.readline().strip()
analizar_cadena(entrada, tabla, grammar, inicio)
