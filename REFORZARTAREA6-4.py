frutas = []
for i in range(4):
    pro = input(f"que frutas agregas a la lista? {i + 1},- ")
    frutas.append(pro)
for i , fruta in enumerate(frutas):
    print(f" {i + 1} {fruta}")
for i in range(len(frutas)-1, -1, -1):
    print(frutas[i])