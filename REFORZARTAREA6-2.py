ListaNumeros = []
for i in range(5):
    num = float(input(f"cuale es tu numero  { i + 1 } "))
    ListaNumeros.append(num)
for i, numero in enumerate(ListaNumeros):
    print(f" {i + 1}.- {numero}")
print(f" la suma de todos es {sum(ListaNumeros)} ")