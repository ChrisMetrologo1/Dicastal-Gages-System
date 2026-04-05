import customtkinter as ctk
import sqlite3
import pandas as pd
from datetime import datetime
from tkinter import messagebox, filedialog

# --- CONFIGURACIÓN VISUAL ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppGages(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Dicastal México - Gestión Pro v6.9 (Columnas Alineadas)")
        self.geometry("1300x900")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="DICASTAL DMXII", font=("Roboto", 24, "bold")).pack(pady=20)
        
        ctk.CTkButton(self.sidebar, text="+ AGREGAR NUEVO", fg_color="#2980B9", command=self.ventana_nuevo_gage).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="📥 IMPORTAR EXCEL", fg_color="#8E44AD", command=self.importar_excel_masivo).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Refrescar Inventario", command=self.cargar_datos).pack(pady=5, padx=20)
        
        ctk.CTkLabel(self.sidebar, text="Reportes Excel", font=("Roboto", 12, "bold")).pack(pady=(30,5))
        ctk.CTkButton(self.sidebar, text="LISTA COMPLETA", fg_color="#27AE60", command=lambda: self.exportar_especifico("completo")).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="SOLO VENCIDOS", fg_color="#C0392B", command=lambda: self.exportar_especifico("vencidos")).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="PRÓXIMOS (30 DÍAS)", fg_color="#E67E22", command=lambda: self.exportar_especifico("proximos")).pack(pady=5, padx=20)

        # --- PANEL PRINCIPAL ---
        self.main = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Tarjetas Interactivas
        self.stats_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 20))
        self.card_ok = self.crear_tarjeta_interactiva(self.stats_frame, "EQUIPOS OK", "#2ECC71", self.filtrar_ok)
        self.card_warn = self.crear_tarjeta_interactiva(self.stats_frame, "PRÓXIMOS (15D)", "#F1C40F", self.filtrar_proximos_15)
        self.card_crit = self.crear_tarjeta_interactiva(self.stats_frame, "VENCIDOS", "#E74C3C", self.filtrar_vencidos)

        # Buscador
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.buscar_en_vivo)
        self.entry_search = ctk.CTkEntry(self.main, placeholder_text="🔍 Buscar por ID, Cliente o Descripción...", width=600, height=40)
        self.entry_search.configure(textvariable=self.search_var)
        self.entry_search.pack(pady=10)

        # --- CABECERA DE LA TABLA (Alineación Fija) ---
        self.header_frame = ctk.CTkFrame(self.main, fg_color="#2C3E50", height=40)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Definimos los mismos pesos para la cabecera y las filas
        self.column_weights = [2, 3, 3, 2] 
        headers = ["ID GAGE", "CLIENTE", "DESCRIPCIÓN", "ESTADO"]
        
        for i, text in enumerate(headers):
            self.header_frame.grid_columnconfigure(i, weight=self.column_weights[i])
            ctk.CTkLabel(self.header_frame, text=text, font=("Roboto", 13, "bold"), text_color="white").grid(row=0, column=i, padx=10, sticky="w")

        self.tabla_container = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.tabla_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.cargar_datos()

    def crear_tarjeta_interactiva(self, master, titulo, color, comando):
        f = ctk.CTkFrame(master, fg_color="#2C3E50", corner_radius=10, cursor="hand2")
        f.pack(side="left", padx=10, expand=True, fill="both")
        f.bind("<Button-1>", lambda e: comando())
        l_tit = ctk.CTkLabel(f, text=titulo, font=("Roboto", 12, "bold"), text_color=color)
        l_tit.pack(pady=(10,0))
        l_num = ctk.CTkLabel(f, text="0", font=("Roboto", 32, "bold"), text_color="white")
        l_num.pack(pady=(0,10))
        l_num.bind("<Button-1>", lambda e: comando())
        return l_num

    def mostrar_datos(self, df_filtro):
        for w in self.tabla_container.winfo_children(): w.destroy()
        
        # Actualizar contadores de las tarjetas
        vencidos = len(self.df_maestro[self.df_maestro['dias'] <= 0])
        proximos = len(self.df_maestro[(self.df_maestro['dias'] > 0) & (self.df_maestro['dias'] <= 15)])
        ok = len(self.df_maestro[self.df_maestro['dias'] > 15])
        self.card_ok.configure(text=str(ok))
        self.card_warn.configure(text=str(proximos))
        self.card_crit.configure(text=str(vencidos))

        for idx, r in df_filtro.head(100).iterrows():
            dias = r['dias'] if pd.notnull(r['dias']) else 999
            color = "#E74C3C" if dias <= 0 else ("#F1C40F" if dias <= 15 else "#2ECC71")
            
            fila = ctk.CTkFrame(self.tabla_container, fg_color="transparent")
            fila.pack(fill="x", pady=2)
            
            # Aplicar pesos de columna a cada fila para que todo se alinee
            for i in range(4): fila.grid_columnconfigure(i, weight=self.column_weights[i])

            r_dict = r.to_dict()
            def abrir_edicion(event, d=r_dict): self.ventana_editar(d)

            # Contenido de la fila
            datos_fila = [
                str(r['id_medicion']),
                str(r['cliente']),
                str(r['descripcion']),
                f"{int(dias)} d" if dias < 400 else "---"
            ]

            for i, texto in enumerate(datos_fila):
                l = ctk.CTkLabel(fila, text=texto, anchor="w")
                if i == 3: l.configure(text_color=color, font=("Roboto", 12, "bold"))
                l.grid(row=0, column=i, padx=10, sticky="w")
                l.bind("<Double-1>", abrir_edicion)

    # --- RESTO DE FUNCIONES (VIRTUALMENTE IGUALES PERO CON CORRECCIONES) ---
    def obtener_datos(self):
        try:
            conn = sqlite3.connect('inventario_gages.db')
            df = pd.read_sql_query("SELECT rowid, id_medicion, cliente, descripcion, ultima_calibracion FROM gages", conn)
            conn.close()
            df['ultima_calibracion'] = pd.to_datetime(df['ultima_calibracion'], errors='coerce')
            df['vence'] = df['ultima_calibracion'] + pd.DateOffset(years=1)
            df['dias'] = (df['vence'] - pd.Timestamp.now().normalize()).dt.days
            return df
        except Exception: return pd.DataFrame()

    def ventana_editar(self, r_data):
        v = ctk.CTkToplevel(self); v.title("Gestión"); v.geometry("400x600"); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="EDITAR EQUIPO", font=("Roboto", 20, "bold")).pack(pady=20)
        
        e_id = ctk.CTkEntry(v, width=280); e_id.insert(0, str(r_data['id_medicion'])); e_id.pack(pady=5)
        e_de = ctk.CTkEntry(v, width=280); e_de.insert(0, str(r_data['descripcion'])); e_de.pack(pady=5)
        
        ctk.CTkLabel(v, text="Fecha (AAAA-MM-DD):").pack(pady=(10,0))
        e_fe = ctk.CTkEntry(v, width=280)
        f_str = r_data['ultima_calibracion'].strftime('%Y-%m-%d') if pd.notnull(r_data['ultima_calibracion']) else ""
        e_fe.insert(0, f_str); e_fe.pack(pady=5)

        def salvar():
            conn = sqlite3.connect('inventario_gages.db'); cursor = conn.cursor()
            cursor.execute("UPDATE gages SET id_medicion=?, descripcion=?, ultima_calibracion=? WHERE rowid=?", 
                           (e_id.get().upper(), e_de.get().upper(), e_fe.get(), r_data['rowid']))
            conn.commit(); conn.close(); v.destroy(); self.cargar_datos()

        ctk.CTkButton(v, text="GUARDAR", fg_color="#27AE60", command=salvar).pack(pady=20)
        ctk.CTkButton(v, text="ELIMINAR", fg_color="#C0392B", command=lambda: self.confirmar_borrar(r_data['rowid'], v)).pack(pady=5)

    def confirmar_borrar(self, rowid, ventana):
        if messagebox.askyesno("Confirmar", "¿Eliminar registro?"):
            conn = sqlite3.connect('inventario_gages.db'); cursor = conn.cursor()
            cursor.execute("DELETE FROM gages WHERE rowid=?", (rowid,))
            conn.commit(); conn.close(); ventana.destroy(); self.cargar_datos()

    def ventana_nuevo_gage(self):
        v = ctk.CTkToplevel(self); v.title("Nuevo"); v.geometry("400x500"); v.attributes("-topmost", True)
        e_id = ctk.CTkEntry(v, placeholder_text="ID GAGE", width=280); e_id.pack(pady=10)
        e_cl = ctk.CTkEntry(v, placeholder_text="CLIENTE", width=280); e_cl.pack(pady=10)
        e_de = ctk.CTkEntry(v, placeholder_text="DESC", width=280); e_de.pack(pady=10)
        e_fe = ctk.CTkEntry(v, width=280); e_fe.insert(0, datetime.now().strftime("%Y-%m-%d")); e_fe.pack(pady=10)
        def add():
            conn = sqlite3.connect('inventario_gages.db'); cursor = conn.cursor()
            cursor.execute("INSERT INTO gages (id_medicion, cliente, descripcion, ultima_calibracion) VALUES (?,?,?,?)", 
                           (e_id.get().upper(), e_cl.get().upper(), e_de.get().upper(), e_fe.get()))
            conn.commit(); conn.close(); v.destroy(); self.cargar_datos()
        ctk.CTkButton(v, text="AÑADIR", command=add).pack(pady=20)

    def importar_excel_masivo(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not ruta: return
        try:
            df_nuevo = pd.read_excel(ruta)
            columnas = ['id_medicion', 'cliente', 'descripcion', 'ultima_calibracion']
            if all(c in df_nuevo.columns for c in columnas):
                conn = sqlite3.connect('inventario_gages.db')
                df_nuevo[columnas].to_sql('gages', conn, if_exists='append', index=False)
                conn.close(); self.cargar_datos(); messagebox.showinfo("OK", "Importado")
        except Exception as e: messagebox.showerror("Error", str(e))

    def exportar_especifico(self, tipo):
        fecha = datetime.now().strftime('%d_%m_%Y')
        if tipo == "completo": df, nom = self.df_maestro, f"Inventario_{fecha}.xlsx"
        elif tipo == "vencidos": df, nom = self.df_maestro[self.df_maestro['dias'] <= 0], f"Vencidos_{fecha}.xlsx"
        elif tipo == "proximos": df, nom = self.df_maestro[(self.df_maestro['dias'] > 0) & (self.df_maestro['dias'] <= 30)], f"Proximos_{fecha}.xlsx"
        df.to_excel(nom, index=False); messagebox.showinfo("OK", f"Excel generado: {nom}")

    def filtrar_ok(self): self.mostrar_datos(self.df_maestro[self.df_maestro['dias'] > 15])
    def filtrar_proximos_15(self): self.mostrar_datos(self.df_maestro[(self.df_maestro['dias'] > 0) & (self.df_maestro['dias'] <= 15)])
    def filtrar_vencidos(self): self.mostrar_datos(self.df_maestro[self.df_maestro['dias'] <= 0])
    def cargar_datos(self): self.df_maestro = self.obtener_datos(); self.mostrar_datos(self.df_maestro)
    def buscar_en_vivo(self, *args):
        t = self.search_var.get().upper()
        self.mostrar_datos(self.df_maestro[(self.df_maestro['id_medicion'].astype(str).str.contains(t, na=False)) | (self.df_maestro['cliente'].astype(str).str.contains(t, na=False))])

if __name__ == "__main__":
    app = AppGages(); app.mainloop()