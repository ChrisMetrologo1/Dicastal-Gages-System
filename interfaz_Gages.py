import customtkinter as ctk
import sqlite3

# Configuración del estilo
ctk.set_appearance_mode("System")  # Detecta si usas modo claro u oscuro en Windows
ctk.set_default_color_theme("blue")

class AppGages(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("Dicastal México - Control de Gages Fase II")
        self.geometry("1000x600")

        # Configurar el cuadrante (layout) 1 fila, 2 columnas
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL (MENÚ) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="DICASTAL", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_inventario = ctk.CTkButton(self.sidebar_frame, text="Inventario (811)", command=self.click_inventario)
        self.btn_inventario.grid(row=1, column=0, padx=20, pady=10)

        self.btn_vencidos = ctk.CTkButton(self.sidebar_frame, text="Ver Vencidos", fg_color="red", command=self.click_vencidos)
        self.btn_vencidos.grid(row=2, column=0, padx=20, pady=10)

        self.btn_excel = ctk.CTkButton(self.sidebar_frame, text="Generar Excel", fg_color="green", command=self.click_excel)
        self.btn_excel.grid(row=3, column=0, padx=20, pady=10)

        # --- ÁREA PRINCIPAL (TABLA Y BUSCADOR) ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.label_titulo = ctk.CTkLabel(self.main_frame, text="Panel de Control de Metrología", font=ctk.CTkFont(size=16))
        self.label_titulo.pack(pady=10)

        # Buscador
        self.entry_busqueda = ctk.CTkEntry(self.main_frame, placeholder_text="Buscar por ID o Cliente...", width=400)
        self.entry_busqueda.pack(pady=10)

        # Aquí irá la tabla de datos más adelante
        self.textbox = ctk.CTkTextbox(self.main_frame, width=700, height=400)
        self.textbox.pack(padx=20, pady=20)
        self.textbox.insert("0.0", "Aquí aparecerán los 811 registros de Dicastal...")

    # --- FUNCIONES DE LOS BOTONES ---
    def click_inventario(self):
        print("Cargando inventario completo...")

    def click_vencidos(self):
        print("Filtrando equipos vencidos...")

    def click_excel(self):
        print("Exportando a Excel...")

if __name__ == "__main__":
    app = AppGages()
    app.mainloop()