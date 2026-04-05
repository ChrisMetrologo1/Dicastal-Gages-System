import customtkinter as ctk
import sqlite3
import pandas as pd
from datetime import datetime
from tkinter import messagebox

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppGages(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Dicastal México - Gestión de Gages v3.5")
        self.geometry("1300x800")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="DICASTAL DMXII", font=("Roboto", 24, "bold")).pack(pady=20)
        
        # BOTÓN NUEVO GAGE (Lo que faltaba)
        self.btn_nuevo = ctk.CTkButton(self.sidebar, text="+ AGREGAR NUEVO", fg_color="#2980B9", hover_color="#1F618D", command=self.ventana_nuevo_gage)
        self.btn_nuevo.pack(pady=15, padx=20)

        ctk.CTkButton(self.sidebar, text="Refrescar Inventario", command=self.cargar_datos).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="VER VENCIDOS", fg_color="#E74C3C", command=self.filtrar_vencidos).pack(pady=5, padx=20)
        
        ctk.CTkLabel(self.sidebar, text="Filtros Rápidos", font=("Roboto", 12, "bold")).pack(pady=(20,5))
        for cliente in ["TESLA", "NISSAN", "STELLANTIS", "VOLKSWAGEN"]:
            ctk.CTkButton(self.sidebar, text=cliente, fg_color="#34495E", height=28, 
                          command=lambda c=cliente: self.filtrar_por_cliente(c)).pack(pady=5, padx=30)

        ctk.CTkButton(self.sidebar, text="Exportar Excel", fg_color="#27AE60", command=self.exportar_excel).pack(side="bottom", pady=20, padx=20)

        # --- PANEL PRINCIPAL ---
        self.main = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.buscar_en_vivo)
        self.entry_search = ctk.CTkEntry(self.main, placeholder_text="🔍 Buscar...", width=600, height=40)
        self.entry_search.configure(textvariable=self.search_var)
        self.entry_search.pack(pady=10)

        self.lbl_contador = ctk.CTkLabel(self.main, text="Mostrando: 0 de 811", font=("Roboto", 11))
        self.lbl_contador.pack(pady=0)

        # CABECERA
        self.header_frame = ctk.CTkFrame(self.main, fg_color="#2C3E50", height=45)
        self.header_frame.pack(fill="x", padx=10, pady=(10,0))
        for i, (txt, w) in enumerate([("ID GAGE", 2), ("CLIENTE", 3), ("DESCRIPCIÓN", 3), ("ESTADO", 2)]):
            self.header_frame.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(self.header_frame, text=txt, font=("Roboto", 13, "bold"), text_color="white").grid(row=0, column=i, padx=15, sticky="w")

        self.tabla_container = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.tabla_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.cargar_datos()

    # --- NUEVA VENTANA PARA AGREGAR ---
    def ventana_nuevo_gage(self):
        v = ctk.CTkToplevel(self)
        v.title("Registro de Nuevo Gage")
        v.geometry("450x550")
        v.attributes("-topmost", True)

        ctk.CTkLabel(v, text="DATOS DEL EQUIPO", font=("Roboto", 20, "bold")).pack(pady=20)
        
        ent_id = ctk.CTkEntry(v, placeholder_text="ID de Medición (Ej: DNmLG-102287)", width=300)
        ent_id.pack(pady=10)
        
        ent_cte = ctk.CTkEntry(v, placeholder_text="Cliente (Ej: TESLA)", width=300)
        ent_cte.pack(pady=10)
        
        ent_desc = ctk.CTkEntry(v, placeholder_text="Descripción", width=300)
        ent_desc.pack(pady=10)
        
        ent_fecha = ctk.CTkEntry(v, placeholder_text="Última Calibración (AAAA-MM-DD)", width=300)
        ent_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ent_fecha.pack(pady=10)

        def guardar_nuevo():
            if not ent_id.get() or not ent_cte.get():
                messagebox.showwarning("Atención", "El ID y el Cliente son obligatorios.")
                return
            
            try:
                conn = sqlite3.connect('inventario_gages.db')
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO gages (id_medicion, cliente, descripcion, ultima_calibracion) 
                               VALUES (?, ?, ?, ?)""", 
                               (ent_id.get().upper(), ent_cte.get().upper(), ent_desc.get().upper(), ent_fecha.get()))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Nuevo gage registrado en la base de datos.")
                v.destroy()
                self.cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"¿Quizás el ID ya existe?\nError: {e}")

        ctk.CTkButton(v, text="REGISTRAR EN SISTEMA", fg_color="green", command=guardar_nuevo).pack(pady=30)

    def ventana_editar(self, id_gage):
        ventana = ctk.CTkToplevel(self)
        ventana.title(f"Calibración: {id_gage}")
        ventana.geometry("400x350")
        ventana.attributes("-topmost", True)

        ctk.CTkLabel(ventana, text="ACTUALIZAR FECHA", font=("Roboto", 18, "bold")).pack(pady=20)
        ctk.CTkLabel(ventana, text=f"ID: {id_gage}").pack()
        
        nueva_fecha = ctk.CTkEntry(ventana, placeholder_text="AAAA-MM-DD")
        nueva_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        nueva_fecha.pack(pady=15)

        def guardar_edit():
            conn = sqlite3.connect('inventario_gages.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE gages SET ultima_calibracion = ? WHERE id_medicion = ?", (nueva_fecha.get(), id_gage))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Fecha actualizada.")
            ventana.destroy()
            self.cargar_datos()

        ctk.CTkButton(ventana, text="GUARDAR CAMBIOS", fg_color="green", command=guardar_edit).pack(pady=20)

    # (Funciones de carga, filtrado y búsqueda se mantienen igual)
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
        for widget in self.tabla_container.winfo_children(): widget.destroy()
        self.lbl_contador.configure(text=f"Mostrando {len(df_filtro.head(60))} de {len(df_filtro)} encontrados (Total Base: {len(self.df_maestro)})")
        for _, r in df_filtro.head(60).iterrows():
            color = "#E74C3C" if r['dias'] <= 0 else ("#F1C40F" if r['dias'] <= 15 else "#2ECC71")
            est = "VENCIDO" if r['dias'] <= 0 else f"{int(r['dias'])} días"
            id_actual = r['id_medicion']
            fila = ctk.CTkFrame(self.tabla_container, fg_color="transparent")
            fila.pack(fill="x", pady=2)
            for i, w in enumerate([2, 3, 3, 2]): fila.grid_columnconfigure(i, weight=w)
            def on_double_click(event, id_g=id_actual): self.ventana_editar(id_g)
            labels = [
                ctk.CTkLabel(fila, text=f"{id_actual}", anchor="w"),
                ctk.CTkLabel(fila, text=f"{str(r['cliente'])[:30]}", anchor="w"),
                ctk.CTkLabel(fila, text=f"{str(r['descripcion'])[:30]}", anchor="w"),
                ctk.CTkLabel(fila, text=est, text_color=color, font=("Roboto", 12, "bold"))
            ]
            fila.bind("<Double-1>", on_double_click)
            for i, lbl in enumerate(labels):
                lbl.grid(row=0, column=i, padx=15, sticky="w")
                lbl.bind("<Double-1>", on_double_click)

    def cargar_datos(self):
        self.df_maestro = self.obtener_datos()
        self.mostrar_datos(self.df_maestro)

    def filtrar_por_cliente(self, cliente):
        res = self.df_maestro[self.df_maestro['cliente'].astype(str).str.contains(cliente, na=False)]
        self.mostrar_datos(res)

    def filtrar_vencidos(self):
        self.mostrar_datos(self.df_maestro[self.df_maestro['dias'] <= 0])

    def buscar_en_vivo(self, *args):
        t = self.search_var.get().upper()
        res = self.df_maestro[(self.df_maestro['id_medicion'].astype(str).str.contains(t)) | 
                              (self.df_maestro['cliente'].astype(str).str.contains(t, na=False))]
        self.mostrar_datos(res)

    def exportar_excel(self):
        nombre = f"Reporte_{datetime.now().strftime('%d_%m')}.xlsx"
        self.df_maestro.to_excel(nombre, index=False)
        messagebox.showinfo("Excel", f"Guardado como: {nombre}")

if __name__ == "__main__":
    app = AppGages()
    app.mainloop()