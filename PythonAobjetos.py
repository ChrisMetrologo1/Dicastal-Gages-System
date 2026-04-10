class Perro:
    raza = 'Aleman'
    
    def __init__(self,tamaño,salud,peso):
        self.tamaño = tamaño
        self.salud = salud
        self.peso = peso
        
    def Atacar(self):
        print(f"el ataca hace una persion de {self.peso/3} de daño ")    







perro_gris = Perro('Grande',150,35)
perro_cafe = Perro('mediano',100,20)
perro_negro = Perro('chico',70,9)


print(f"mi perro de tamaño {perro_gris.tamaño} ataca")
perro_gris.Atacar()

print(f"mi perro de tamaño {perro_negro.tamaño} ataca")
perro_negro.Atacar()

