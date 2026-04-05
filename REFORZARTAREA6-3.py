helados = []
for i in range(3):
    pro = input(F" cual sabor quieres tus helado {i + 1} ")
    helados.append(pro)
for i, sabor in enumerate(helados):
    print(F"{i + 1}.- {sabor}")

    
