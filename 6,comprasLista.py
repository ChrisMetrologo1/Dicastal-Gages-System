lista = []
contador = 0
while contador < 6:
    prducto = (input("Hola soy tu asistente de compras, que productos quieres agregar hoy? "))
    lista.append(prducto)
    print(f"listo tu producto {prducto} se a agregado a la lista exitosamente.")
    for i in enumerate(lista):
        print(f"{i + 1}")
        contador + 1

   

