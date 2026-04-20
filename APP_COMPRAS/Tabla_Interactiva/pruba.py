import pandas as pd
print("pandas funciona")
df = pd.DataFrame({"A": [1,2,3]})
df.to_excel("prueba.xlsx", index=False)
print("Excel creado")