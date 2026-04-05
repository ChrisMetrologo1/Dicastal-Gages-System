frase = input("puedes decirme tu frase? ")
frase = frase.lower()
contador = 0
for letra in frase:
    if letra == "a" or letra == "e" or letra == "i" or letra == "u" or letra == "o":
        contador = contador + 1
print(f" la frase tiene {contador} vocales. ")