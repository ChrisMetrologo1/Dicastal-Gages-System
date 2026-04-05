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

        self.title("Dicastal México - Gestión de Gages v5.0")
        self.geometry("1300x850")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="DICASTAL DMXII", font=("Roboto", 24, "bold")).pack(pady=20)
        
        self.btn_nuevo = ctk.CTkButton(self.sidebar, text="+ AGREGAR NUEVO", fg_color="#2980B9", hover_color="#1F618D", command=self.ventana_nuevo_gage)
        self.btn_nuevo.pack(pady=10, padx=20)

        ctk.CTkButton(self.sidebar, text="Refrescar Inventario", command=self.cargar_datos).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="VER VENCIDOS", fg_color="#E74C3C", command=self.filtrar_vencidos).pack(pady=5, padx=20)
        
        ctk.CTkLabel(self.sidebar, text="Filtros Rápidos", font=("Roboto", 12, "bold")).pack(pady=(20,5))
        for cliente in ["TESLA", "NISSAN", "STELLANTIS", "VOLKSWAGEN"]:
            ctk.CTkButton(self.sidebar, text=cliente, fg_color="#34495E", height=28, 
                          command=lambda c=cliente: self.filtrar_por_cliente(c)).pack(pady=5, padx=30)

        # --- SECCIÓN DE REPORTES ---
        ctk.CTkLabel(self.sidebar, text="Reportes Excel", font=("Roboto", 12, "bold")).pack(pady=(30,5))
        ctk.CTkButton(self.sidebar, text="LISTA COMPLETA", fg_color="#27AE60", command=lambda: self.exportar_especifico("completo")).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="SOLO VENCIDOS", fg_color="#C0392B", command=lambda: self.exportar_especifico("vencidos")).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="PRÓXIMOS (30 DÍAS)", fg_color="#F39C12", command=lambda: self.exportar_especifico("proximos")).pack(pady=5, padx=20)

        # --- PANEL PRINCIPAL ---
        self.main = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.buscar_en_vivo)
        self.entry_search = ctk.CTkEntry(self.main, placeholder_text="🔍 Buscar por ID, Cliente o Descripción...", width=600, height=40)
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
            # Seleccionamos ROWID para tener una llave única y evitar errores de edición
            df = pd.read_sql_query("SELECT rowid, id_medicion, cliente, descripcion, ultima_calibracion FROM gages", conn)
            conn.close()
            df['ultima_calibracion'] = pd.to_datetime(df['ultima_calibracion'], errors='coerce')
            df['vence'] = df['ultima_calibracion'] + pd.DateOffset(years=1)
            df['dias'] = (df['vence'] - pd.Timestamp.now().normalize()).dt.days
            return df
        except Exception:
            return pd.DataFrame()

    def mostrar_datos(self, df_filtro):
        for widget in self.tabla_container.winfo_children(): widget.destroy()
        total_base = len(self.df_maestro) if hasattr(self, 'df_maestro') else 0
        self.lbl_contador.configure(text=f"Mostrando {len(df_filtro.head(100))} de {len(df_filtro)} encontrados (Total Base: {total_base})")
        
        for idx, r in df_filtro.head(100).iterrows():
            dias = r['dias'] if pd.notnull(r['dias']) else 999
            color = "#E74C3C" if dias <= 0 else ("#F1C40F" if dias <= 15 else "#2ECC71")
            est = "VENCIDO" if dias <= 0 else f"{int(dias)} días"
            
            # Limpieza visual de valores 'nan'
            id_val = str(r['id_medicion']).strip()
            es_nan = id_val.lower() in ["nan", "none", "", "nan.0"]
            id_display = "--- (SIN ID) ---" if es_nan else id_val
            
            cliente_val = "S/N" if str(r['cliente']).lower() in ["nan", "none"] else str(r['cliente'])
            desc_val = "S/N" if str(r['descripcion']).lower() in ["nan", "none"] else str(r['descripcion'])

            r_dict = r.to_dict()
            fila = ctk.CTkFrame(self.tabla_container, fg_color="transparent")
            fila.pack(fill="x", pady=2)
            for i, w in enumerate([2, 3, 3, 2]): fila.grid_columnconfigure(i, weight=w)
            
            def abrir_edicion(event, data=r_dict): self.ventana_editar(data)
            
            lbls = [
                ctk.CTkLabel(fila, text=id_display, anchor="w", text_color="#3498DB" if es_nan else "white"),
                ctk.CTkLabel(fila, text=f"{cliente_val[:30]}", anchor="w"),
                ctk.CTkLabel(fila, text=f"{desc_val[:30]}", anchor="w"),
                ctk.CTkLabel(fila, text=est, text_color=color, font=("Roboto", 12, "bold"))
            ]
            for i, l in enumerate(lbls):
                l.grid(row=0, column=i, padx=15, sticky="w")
                l.bind("<Double-1>", abrir_edicion)
            fila.bind("<Double-1>", abrir_edicion)

    def cargar_datos(self):
        self.df_maestro = self.obtener_datos()
        self.mostrar_datos(self.df_maestro)

    # --- VENTANA DE GESTIÓN (SIN ERROR DE LIMIT) ---
    def ventana_editar(self, r_data):
        v = ctk.CTkToplevel(self)
        v.title("Gestor de Gages")
        v.geometry("400x650")
        v.attributes("-topmost", True)

        ctk.CTkLabel(v, text="CENTRO DE CONTROL", font=("Roboto", 20, "bold")).pack(pady=20)
        
        # ID
        ctk.CTkLabel(v, text="ID del Gage:").pack()
        ent_id = ctk.CTkEntry(v, width=280)
        id_init = "" if str(r_data['id_medicion']).lower() in ["nan", "none", "nan.0"] else str(r_data['id_medicion'])
        ent_id.insert(0, id_init)
        ent_id.pack(pady=5)

        # Descripción
        ctk.CTkLabel(v, text="\nDescripción / Medida:").pack()
        ent_desc = ctk.CTkEntry(v, width=280)
        desc_init = "" if str(r_data['descripcion']).lower() in ["nan", "none"] else str(r_data['descripcion'])
        ent_desc.insert(0, desc_init)
        ent_desc.pack(pady=5)

        # Fecha
        ctk.CTkLabel(v, text="\nÚltima Calibración (AAAA-MM-DD):").pack()
        ent_fecha = ctk.CTkEntry(v, width=280)
        f_s = r_data['ultima_calibracion'].strftime('%Y-%m-%d') if pd.notnull(r_data['ultima_calibracion']) else datetime.now().strftime("%Y-%m-%d")
        ent_fecha.insert(0, f_s)
        ent_fecha.pack(pady=5)

        def guardar():
            n_id, n_desc, n_fecha = ent_id.get().strip().upper(), ent_desc.get().strip().upper(), ent_fecha.get().strip()
            try:
                conn = sqlite3.connect('inventario_gages.db')
                cursor = conn.cursor()
                # Usamos ROWID para actualizar exactamente la fila que seleccionamos
                cursor.execute("UPDATE gages SET id_medicion=?, descripcion=?, ultima_calibracion=? WHERE rowid=?", 
                               (n_id, n_desc, n_fecha, r_data['rowid']))
                conn.commit()
                conn.close()
                v.destroy()
                self.cargar_datos()
            except Exception as e: messagebox.showerror("Error", f"No se pudo guardar: {e}")

        def eliminar():
            if messagebox.askyesno("⚠️ ELIMINAR", "¿Borrar este gage del sistema?"):
                try:
                    conn = sqlite3.connect('inventario_gages.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM gages WHERE rowid=?", (r_data['rowid'],))
                    conn.commit()
                    conn.close()
                    v.destroy()
                    self.cargar_datos()
                except Exception as e: messagebox.showerror("Error", str(e))

        ctk.CTkButton(v, text="GUARDAR CAMBIOS", fg_color="#27AE60", command=guardar).pack(pady=20)
        ctk.CTkButton(v, text="🗑️ ELIMINAR REGISTRO", fg_color="#C0392B", command=eliminar).pack(pady=10)

    # --- OTRAS FUNCIONES ---
    def ventana_nuevo_gage(self):
        v = ctk.CTkToplevel(self); v.title("Nuevo Gage"); v.geometry("450x550"); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="ALTA DE EQUIPO", font=("Roboto", 20, "bold")).pack(pady=20)
        e_id = ctk.CTkEntry(v, placeholder_text="ID GAGE", width=300); e_id.pack(pady=10)
        e_cl = ctk.CTkEntry(v, placeholder_text="CLIENTE", width=300); e_cl.pack(pady=10)
        e_de = ctk.CTkEntry(v, placeholder_text="DESCRIPCIÓN", width=300); e_de.pack(pady=10)
        e_fe = ctk.CTkEntry(v, width=300); e_fe.insert(0, datetime.now().strftime("%Y-%m-%d")); e_fe.pack(pady=10)
        def registrar():
            conn = sqlite3.connect('inventario_gages.db'); cursor = conn.cursor()
            cursor.execute("INSERT INTO gages (id_medicion, cliente, descripcion, ultima_calibracion) VALUES (?,?,?,?)", (e_id.get().upper(), e_cl.get().upper(), e_de.get().upper(), e_fe.get()))
            conn.commit(); conn.close(); v.destroy(); self.cargar_datos()
        ctk.CTkButton(v, text="AÑADIR", fg_color="#2980B9", command=registrar).pack(pady=30)

    def exportar_especifico(self, tipo):
        fecha = datetime.now().strftime('%d_%m_%Y')
        if tipo == "completo": df, nom = self.df_maestro, f"Inventario_Completo_{fecha}.xlsx"
        elif tipo == "vencidos": df, nom = self.df_maestro[self.df_maestro['dias'] <= 0], f"VENCIDOS_{fecha}.xlsx"
        elif tipo == "proximos": df, nom = self.df_maestro[(self.df_maestro['dias'] > 0) & (self.df_maestro['dias'] <= 30)], f"PROXIMOS_30DIAS_{fecha}.xlsx"
        if df.empty: return
        df.to_excel(nom, index=False)
        messagebox.showinfo("Éxito", f"Archivo generado: {nom}")

    def filtrar_por_cliente(self, c): self.mostrar_datos(self.df_maestro[self.df_maestro['cliente'].astype(str).str.contains(c, na=False)])
    def filtrar_vencidos(self): self.mostrar_datos(self.df_maestro[self.df_maestro['dias'] <= 0])
    def buscar_en_vivo(self, *args):
        t = self.search_var.get().upper()
        self.mostrar_datos(self.df_maestro[(self.df_maestro['id_medicion'].astype(str).str.contains(t, na=False)) | (self.df_maestro['cliente'].astype(str).str.contains(t, na=False)) | (self.df_maestro['descripcion'].astype(str).str.contains(t, na=False))])

if __name__ == "__main__":
    app = AppGages(); app.mainloop()
    