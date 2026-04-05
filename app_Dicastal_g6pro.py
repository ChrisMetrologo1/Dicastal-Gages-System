import customtkinter as ctk
import sqlite3
import pandas as pd
from datetime import datetime
from tkinter import messagebox

# --- CONFIGURACIÓN VISUAL ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppGages(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Dicastal México - Gestión de Gages v4.0")
        self.geometry("1300x850")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="DICASTAL DMXII", font=("Roboto", 24, "bold")).pack(pady=20)
        
        self.btn_nuevo = ctk.CTkButton(self.sidebar, text="+ AGREGAR NUEVO", fg_color="#2980B9", hover_color="#1F618D", command=self.ventana_nuevo_gage)
        self.btn_nuevo.pack(pady=10, padx=20)

        self.btn_id_manager = ctk.CTkButton(self.sidebar, text="⚙️ CAMBIO INGENIERÍA", fg_color="#8E44AD", hover_color="#7D3C98", command=self.ventana_gestionar_id)
        self.btn_id_manager.pack(pady=10, padx=20)

        ctk.CTkButton(self.sidebar, text="Refrescar Inventario", command=self.cargar_datos).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="VER VENCIDOS", fg_color="#E74C3C", command=self.filtrar_vencidos).pack(pady=5, padx=20)
        
        ctk.CTkLabel(self.sidebar, text="Filtros Rápidos", font=("Roboto", 12, "bold")).pack(pady=(20,5))
        for cliente in ["TESLA", "NISSAN", "STELLANTIS", "VOLKSWAGEN"]:
            ctk.CTkButton(self.sidebar, text=cliente, fg_color="#34495E", height=28, 
                          command=lambda c=cliente: self.filtrar_por_cliente(c)).pack(pady=5, padx=30)

        # --- SECCIÓN DE EXPORTACIÓN (NUEVA) ---
        ctk.CTkLabel(self.sidebar, text="Reportes Excel", font=("Roboto", 12, "bold")).pack(pady=(30,5))
        
        ctk.CTkButton(self.sidebar, text="LISTA COMPLETA", fg_color="#27AE60", command=lambda: self.exportar_especifico("completo")).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="SOLO VENCIDOS", fg_color="#C0392B", command=lambda: self.exportar_especifico("vencidos")).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="PRÓXIMOS (30 DÍAS)", fg_color="#F39C12", command=lambda: self.exportar_especifico("proximos")).pack(pady=5, padx=20)

        # --- PANEL PRINCIPAL ---
        self.main = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.buscar_en_vivo)
        self.entry_search = ctk.CTkEntry(self.main, placeholder_text="🔍 Buscar por ID o Cliente...", width=600, height=40)
        self.entry_search.configure(textvariable=self.search_var)
        self.entry_search.pack(pady=10)

        self.lbl_contador = ctk.CTkLabel(self.main, text="Iniciando...", font=("Roboto", 11))
        self.lbl_contador.pack(pady=0)

        # CABECERA DE TABLA
        self.header_frame = ctk.CTkFrame(self.main, fg_color="#2C3E50", height=45)
        self.header_frame.pack(fill="x", padx=10, pady=(10,0))
        
        columnas = [("ID GAGE", 0, 2), ("CLIENTE", 1, 3), ("DESCRIPCIÓN", 2, 3), ("ESTADO", 3, 2)]
        for texto, col, peso in columnas:
            self.header_frame.grid_columnconfigure(col, weight=peso)
            ctk.CTkLabel(self.header_frame, text=texto, font=("Roboto", 13, "bold"), text_color="white").grid(row=0, column=col, padx=15, sticky="w")

        self.tabla_container = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.tabla_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.cargar_datos()

    # --- LÓGICA DE DATOS ---
    def obtener_datos(self):
        try:
            conn = sqlite3.connect('inventario_gages.db')
            df = pd.read_sql_query("SELECT id_medicion, cliente, descripcion, ultima_calibracion FROM gages", conn)
            conn.close()
            df['ultima_calibracion'] = pd.to_datetime(df['ultima_calibracion'], errors='coerce')
            df['vence'] = df['ultima_calibracion'] + pd.DateOffset(years=1)
            df['dias'] = (df['vence'] - pd.Timestamp.now().normalize()).dt.days
            return df
        except Exception as e:
            return pd.DataFrame()

    def mostrar_datos(self, df_filtro):
        for widget in self.tabla_container.winfo_children(): widget.destroy()
        total_base = len(self.df_maestro) if hasattr(self, 'df_maestro') else 0
        self.lbl_contador.configure(text=f"Mostrando {len(df_filtro.head(60))} de {len(df_filtro)} encontrados (Total Base: {total_base})")
        
        for _, r in df_filtro.head(60).iterrows():
            dias = r['dias'] if pd.notnull(r['dias']) else 999
            color = "#E74C3C" if dias <= 0 else ("#F1C40F" if dias <= 15 else "#2ECC71")
            est = "VENCIDO" if dias <= 0 else f"{int(dias)} días"
            id_val = r['id_medicion']
            es_nan = pd.isna(id_val) or str(id_val).lower() == "nan" or id_val == ""
            id_display = "--- (SIN ID) ---" if es_nan else id_val
            r_data = r.to_dict()
            fila = ctk.CTkFrame(self.tabla_container, fg_color="transparent")
            fila.pack(fill="x", pady=2)
            for i, w in enumerate([2, 3, 3, 2]): fila.grid_columnconfigure(i, weight=w)
            def on_double_click(event, data=r_data): self.ventana_editar(data)
            lbls = [
                ctk.CTkLabel(fila, text=id_display, anchor="w", text_color="#3498DB" if es_nan else "white"),
                ctk.CTkLabel(fila, text=f"{str(r['cliente'])[:25]}", anchor="w"),
                ctk.CTkLabel(fila, text=f"{str(r['descripcion'])[:25]}", anchor="w"),
                ctk.CTkLabel(fila, text=est, text_color=color, font=("Roboto", 12, "bold"))
            ]
            for i, l in enumerate(lbls):
                l.grid(row=0, column=i, padx=15, sticky="w")
                l.bind("<Double-1>", on_double_click)
            fila.bind("<Double-1>", on_double_click)

    def cargar_datos(self):
        self.df_maestro = self.obtener_datos()
        self.mostrar_datos(self.df_maestro)

    # --- EXPORTACIÓN MEJORADA ---
    def exportar_especifico(self, tipo):
        fecha_str = datetime.now().strftime('%d_%m_%Y')
        if tipo == "completo":
            df_final = self.df_maestro
            nombre = f"Inventario_Completo_{fecha_str}.xlsx"
        elif tipo == "vencidos":
            df_final = self.df_maestro[self.df_maestro['dias'] <= 0]
            nombre = f"Reporte_VENCIDOS_{fecha_str}.xlsx"
        elif tipo == "proximos":
            df_final = self.df_maestro[(self.df_maestro['dias'] > 0) & (self.df_maestro['dias'] <= 30)]
            nombre = f"Reporte_PROXIMOS_30DIAS_{fecha_str}.xlsx"

        if df_final.empty:
            messagebox.showinfo("Reporte", "No hay datos que coincidan con este reporte.")
            return

        try:
            df_final.to_excel(nombre, index=False)
            messagebox.showinfo("Éxito", f"Archivo generado:\n{nombre}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el Excel: {e}")

    # --- VENTANAS (REUTILIZADAS DE V3.9) ---
    def ventana_editar(self, r_data):
        id_actual = r_data['id_medicion']
        v = ctk.CTkToplevel(self)
        v.title("Editor de Gage")
        v.geometry("400x650")
        v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="GESTIÓN DE EQUIPO", font=("Roboto", 20, "bold")).pack(pady=20)
        ent_id = ctk.CTkEntry(v, width=280); ent_id.insert(0, "" if pd.isna(id_actual) else id_actual); ent_id.pack(pady=5)
        ent_desc = ctk.CTkEntry(v, width=280); ent_desc.insert(0, "" if pd.isna(r_data['descripcion']) else r_data['descripcion']); ent_desc.pack(pady=5)
        ent_fecha = ctk.CTkEntry(v, width=280); f_s = r_data['ultima_calibracion'].strftime('%Y-%m-%d') if pd.notnull(r_data['ultima_calibracion']) else datetime.now().strftime("%Y-%m-%d")
        ent_fecha.insert(0, f_s); ent_fecha.pack(pady=5)

        def guardar():
            conn = sqlite3.connect('inventario_gages.db'); cursor = conn.cursor()
            cursor.execute("UPDATE gages SET id_medicion=?, descripcion=?, ultima_calibracion=? WHERE cliente=? AND descripcion=? AND (id_medicion=? OR id_medicion IS NULL OR id_medicion='') LIMIT 1",
                           (ent_id.get().upper(), ent_desc.get().upper(), ent_fecha.get(), r_data['cliente'], r_data['descripcion'], id_actual))
            conn.commit(); conn.close(); v.destroy(); self.cargar_datos()

        def eliminar():
            if messagebox.askyesno("⚠️ ELIMINAR", "¿Borrar este registro?"):
                conn = sqlite3.connect('inventario_gages.db'); cursor = conn.cursor()
                cursor.execute("DELETE FROM gages WHERE cliente=? AND descripcion=? AND (id_medicion=? OR id_medicion IS NULL OR id_medicion='')", (r_data['cliente'], r_data['descripcion'], id_actual))
                conn.commit(); conn.close(); v.destroy(); self.cargar_datos()

        ctk.CTkButton(v, text="GUARDAR CAMBIOS", fg_color="#27AE60", command=guardar).pack(pady=20)
        ctk.CTkButton(v, text="🗑️ ELIMINAR GAGE", fg_color="#C0392B", command=eliminar).pack(pady=10)

    def ventana_nuevo_gage(self):
        v = ctk.CTkToplevel(self); v.title("Nuevo Registro"); v.geometry("450x550"); v.attributes("-topmost", True)
        e_id = ctk.CTkEntry(v, placeholder_text="ID GAGE", width=300); e_id.pack(pady=10)
        e_cl = ctk.CTkEntry(v, placeholder_text="CLIENTE", width=300); e_cl.pack(pady=10)
        e_de = ctk.CTkEntry(v, placeholder_text="DESCRIPCIÓN", width=300); e_de.pack(pady=10)
        e_fe = ctk.CTkEntry(v, width=300); e_fe.insert(0, datetime.now().strftime("%Y-%m-%d")); e_fe.pack(pady=10)
        def registrar():
            conn = sqlite3.connect('inventario_gages.db'); cursor = conn.cursor()
            cursor.execute("INSERT INTO gages (id_medicion, cliente, descripcion, ultima_calibracion) VALUES (?,?,?,?)", (e_id.get().upper(), e_cl.get().upper(), e_de.get().upper(), e_fe.get()))
            conn.commit(); conn.close(); v.destroy(); self.cargar_datos()
        ctk.CTkButton(v, text="AÑADIR", command=registrar).pack(pady=30)

    def ventana_gestionar_id(self):
        v = ctk.CTkToplevel(self); v.title("Ingeniería"); v.geometry("400x400"); v.attributes("-topmost", True)
        ev = ctk.CTkEntry(v, placeholder_text="ID Actual", width=300); ev.pack(pady=10)
        en = ctk.CTkEntry(v, placeholder_text="Nuevo ID", width=300); en.pack(pady=10)
        def aplicar():
            conn = sqlite3.connect('inventario_gages.db'); cursor = conn.cursor()
            cursor.execute("UPDATE gages SET id_medicion = ? WHERE id_medicion = ?", (en.get().upper(), ev.get().upper()))
            conn.commit(); conn.close(); v.destroy(); self.cargar_datos()
        ctk.CTkButton(v, text="APLICAR", command=aplicar).pack(pady=30)

    def filtrar_por_cliente(self, c): self.mostrar_datos(self.df_maestro[self.df_maestro['cliente'].astype(str).str.contains(c, na=False)])
    def filtrar_vencidos(self): self.mostrar_datos(self.df_maestro[self.df_maestro['dias'] <= 0])
    def buscar_en_vivo(self, *args):
        t = self.search_var.get().upper()
        self.mostrar_datos(self.df_maestro[(self.df_maestro['id_medicion'].astype(str).str.contains(t, na=False)) | (self.df_maestro['cliente'].astype(str).str.contains(t, na=False))])

if __name__ == "__main__":
    app = AppGages(); app.mainloop()