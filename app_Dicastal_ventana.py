import customtkinter as ctk
import sqlite3
import pandas as pd
from datetime import datetime

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppGages(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Dicastal México - Control de Metrología")
        self.geometry("1250x750")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="DICASTAL", font=("Roboto", 24, "bold")).pack(pady=20)
        
        ctk.CTkButton(self.sidebar, text="Refrescar Lista", command=self.cargar_datos).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Ver Vencidos", fg_color="#E74C3C", command=self.filtrar_vencidos).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Exportar Excel", fg_color="#27AE60", command=self.exportar_excel).pack(pady=10, padx=20)

        # --- PANEL PRINCIPAL ---
        self.main = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.buscar_en_vivo)
        self.entry_search = ctk.CTkEntry(self.main, placeholder_text="🔍 Buscar ID o Cliente...", width=600, height=40)
        self.entry_search.configure(textvariable=self.search_var)
        self.entry_search.pack(pady=15)

        # CABECERA FIJA
        self.header_frame = ctk.CTkFrame(self.main, fg_color="#2C3E50", height=45)
        self.header_frame.pack(fill="x", padx=10)
        
        for i, (txt, w) in enumerate([("ID GAGE", 2), ("CLIENTE", 3), ("DESCRIPCIÓN", 3), ("ESTADO", 2)]):
            self.header_frame.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(self.header_frame, text=txt, font=("Roboto", 13, "bold"), text_color="white").grid(row=0, column=i, padx=15, sticky="w")

        # TABLA CON SCROLL
        self.tabla_container = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.tabla_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.cargar_datos()

    def obtener_datos(self):
        try:
            conn = sqlite3.connect('inventario_gages.db')
            df = pd.read_sql_query("SELECT id_medicion, cliente, descripcion, ultima_calibracion FROM gages", conn)
            conn.close()
            df['ultima_calibracion'] = pd.to_datetime(df['ultima_calibracion'])
            df['vence'] = df['ultima_calibracion'] + pd.DateOffset(years=1)
            df['dias'] = (df['vence'] - pd.Timestamp.now().normalize()).dt.days
            return df
        except: return pd.DataFrame()

    def mostrar_datos(self, df_filtro):
        for widget in self.tabla_container.winfo_children():
            widget.destroy()

        # Solo mostramos los primeros 60 para evitar el error de memoria
        # Pero el buscador siempre revisará los 811
        for _, r in df_filtro.head(60).iterrows():
            color = "#E74C3C" if r['dias'] <= 0 else ("#F1C40F" if r['dias'] <= 15 else "#2ECC71")
            est = "VENCIDO" if r['dias'] <= 0 else f"{int(r['dias'])} días"

            fila = ctk.CTkFrame(self.tabla_container, fg_color="transparent")
            fila.pack(fill="x", pady=2)
            for i, w in enumerate([2, 3, 3, 2]): fila.grid_columnconfigure(i, weight=w)
            
            ctk.CTkLabel(fila, text=f"{r['id_medicion']}", anchor="w").grid(row=0, column=0, padx=15, sticky="w")
            ctk.CTkLabel(fila, text=f"{str(r['cliente'])[:30]}", anchor="w").grid(row=0, column=1, padx=15, sticky="w")
            ctk.CTkLabel(fila, text=f"{str(r['descripcion'])[:30]}", anchor="w").grid(row=0, column=2, padx=15, sticky="w")
            ctk.CTkLabel(fila, text=est, text_color=color, font=("Roboto", 12, "bold")).grid(row=0, column=3, padx=15, sticky="w")

    def cargar_datos(self):
        self.df_maestro = self.obtener_datos()
        self.mostrar_datos(self.df_maestro)

    def filtrar_vencidos(self):
        self.mostrar_datos(self.df_maestro[self.df_maestro['dias'] <= 0])

    def buscar_en_vivo(self, *args):
        t = self.search_var.get().upper()
        res = self.df_maestro[(self.df_maestro['id_medicion'].astype(str).str.contains(t)) | 
                              (self.df_maestro['cliente'].astype(str).str.contains(t, na=False))]
        self.mostrar_datos(res)

    def exportar_excel(self):
        self.df_maestro.to_excel(f"Reporte_{datetime.now().strftime('%d_%m')}.xlsx", index=False)

if __name__ == "__main__":
    app = AppGages()
    app.mainloop()