tienda = []
for i in range(5):
    producto = input(f"que es lo que vas a agregar a  tu lista de mercado? { i + 1}  ")
    tienda.append(producto)
for i, pro in enumerate(tienda):
    print(f"{i + 1}.- {pro}")
    