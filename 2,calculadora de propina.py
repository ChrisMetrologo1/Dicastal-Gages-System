name = input("como te llamas? ")
numcoma= int(input(f"{name} puedes decirme el numero de tu orden? "))
total = float(input(f"{name} cuanto es el total de tu compra? "))
propina = int(input(f"{name} cuanto gustas dejar de propina 5,10,15? "))
pro = total * propina / 100
total_propina = pro + total
if propina == 5:
    print(f"tu propina fue de {pro} + {total} = {total_propina} ")
    print(f"gracias por tu compra {name} ")
elif  propina == 10:
    print(f"tu propina fue de {pro} + {total} = {total_propina} ")
    print(f"gracias por tu compra {name} ")
else: propina == 15
print(f"tu propina fue de {pro} + {total} = {total_propina} ")
print(f"gracias por tu compra {name} ") 

       
    

