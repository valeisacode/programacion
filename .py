import sqlite3
from tkinter import Tk, Label, Entry, Button, messagebox, Listbox, SINGLE, END, simpledialog
import os


DB_FILE = 'aerolinea1.db'



def inicializar_bd():
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Vuelos (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Origen TEXT NOT NULL,
        Destino TEXT NOT NULL,
        Horario TEXT NOT NULL,
        CapacidadMaxima INTEGER NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Pasajero (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre TEXT NOT NULL,
        Pasaporte TEXT UNIQUE NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Boletos (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        VueloID INTEGER NOT NULL,
        PasajeroID INTEGER NOT NULL,
        Asiento TEXT NOT NULL,
        FOREIGN KEY(VueloID) REFERENCES Vuelos(ID),
        FOREIGN KEY(PasajeroID) REFERENCES Pasajero(ID)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Asientos (
        VueloID INTEGER NOT NULL,
        Asiento TEXT NOT NULL,
        Estado TEXT NOT NULL CHECK(Estado IN ('disponible', 'reservado')),
        PRIMARY KEY (VueloID, Asiento),
        FOREIGN KEY(VueloID) REFERENCES Vuelos(ID)
    )''')

    conexion.commit()
    cursor.close()
    conexion.close()


# Capa datos
def obtener_conexion():
    try:
        conexion = sqlite3.connect(DB_FILE)
        return conexion
    except Exception as e:
        print(f"Error en conexión SQLite: {e}")
        return None


#vuelos
def insertar_vuelo(origen, destino, horario, capacidad):
    conexion = obtener_conexion()
    if conexion is None:
        raise Exception("No se pudo conectar a la base de datos")
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO Vuelos (Origen, Destino, Horario, CapacidadMaxima) VALUES (?, ?, ?, ?)"
        cursor.execute(sql, (origen, destino, horario, capacidad))
        vuelo_id = cursor.lastrowid

        # asientos como disponible
        for i in range(1, capacidad + 1):
            asiento = f"{i}"
            cursor.execute("INSERT INTO Asientos (VueloID, Asiento, Estado) VALUES (?, ?, 'disponible')",
                           (vuelo_id, asiento))

        conexion.commit()
        return vuelo_id
    finally:
        cursor.close()
        conexion.close()


#pasajeros
def insertar_pasajero(nombre, pasaporte):
    conexion = obtener_conexion()
    if conexion is None:
        raise Exception("No se pudo conectar a la base de datos")
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO Pasajero (Nombre, Pasaporte) VALUES (?, ?)"
        cursor.execute(sql, (nombre, pasaporte))
        conexion.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Pasaporte ya registrado")
    finally:
        cursor.close()
        conexion.close()


# CRUD boletos
def insertar_boleto(id_vuelo, id_pasajero, asiento):
    conexion = obtener_conexion()
    if conexion is None:
        raise Exception("No se pudo conectar a la base de datos")
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO Boletos (VueloID, PasajeroID, Asiento) VALUES (?, ?, ?)"
        cursor.execute(sql, (id_vuelo, id_pasajero, asiento))
        conexion.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conexion.close()


# Gestión asientos
def obtener_asientos_disponibles(id_vuelo):
    conexion = obtener_conexion()
    if conexion is None:
        raise Exception("No conexión a la base de datos")
    cursor = conexion.cursor()
    try:
        sql = "SELECT Asiento FROM Asientos WHERE VueloID = ? AND Estado = 'disponible'"
        cursor.execute(sql, (id_vuelo,))
        resultados = cursor.fetchall()
        return [row[0] for row in resultados]
    finally:
        cursor.close()
        conexion.close()


def reservar_asiento(id_vuelo, asiento):
    conexion = obtener_conexion()
    if conexion is None:
        raise Exception("No conexión a la base de datos")
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT Estado FROM Asientos WHERE VueloID=? AND Asiento=?", (id_vuelo, asiento))
        result = cursor.fetchone()
        if not result or result[0] != "disponible":
            return False, "Asiento no disponible"
        cursor.execute("UPDATE Asientos SET Estado='reservado' WHERE VueloID=? AND Asiento=?", (id_vuelo, asiento))
        conexion.commit()
        return True, "Asiento reservado correctamente"
    finally:
        cursor.close()
        conexion.close()


def eliminar_asiento(id_vuelo, asiento):
    conexion = obtener_conexion()
    if conexion is None:
        raise Exception("No conexión a la base de datos")
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM Asientos WHERE VueloID=? AND Asiento=?", (id_vuelo, asiento))
        conexion.commit()
        return True
    finally:
        cursor.close()
        conexion.close()


# Lógica negocio
def registrar_vuelo(origen, destino, horario, capacidad):
    return insertar_vuelo(origen, destino, horario, capacidad)


def registrar_pasajero(nombre, pasaporte):
    return insertar_pasajero(nombre, pasaporte)


def vender_boleto(id_vuelo, id_pasajero, asiento):
    disponible, msg = reservar_asiento(id_vuelo, asiento)
    if not disponible:
        raise ValueError(msg)
    return insertar_boleto(id_vuelo, id_pasajero, asiento)


# Interfaz gráfica
class InterfazUsuario:
    def __init__(self):
        self.root = Tk()
        self.root.title("Sistema Aerolínea")

        Label(self.root, text="Registrar Pasajero").grid(row=0, columnspan=2)
        Label(self.root, text="Nombre").grid(row=1, column=0)
        self.entry_nombre = Entry(self.root)
        self.entry_nombre.grid(row=1, column=1)
        Label(self.root, text="Pasaporte").grid(row=2, column=0)
        self.entry_pasaporte = Entry(self.root)
        self.entry_pasaporte.grid(row=2, column=1)
        Button(self.root, text="Registrar Pasajero", command=self.registrar_pasajero).grid(row=3, columnspan=2)

        Label(self.root, text="Registrar Vuelo").grid(row=4, columnspan=2)
        Label(self.root, text="Origen").grid(row=5, column=0)
        self.entry_origen = Entry(self.root)
        self.entry_origen.grid(row=5, column=1)
        Label(self.root, text="Destino").grid(row=6, column=0)
        self.entry_destino = Entry(self.root)
        self.entry_destino.grid(row=6, column=1)
        Label(self.root, text="Horario (YYYY-MM-DD HH:MM:SS)").grid(row=7, column=0)
        self.entry_horario = Entry(self.root)
        self.entry_horario.grid(row=7, column=1)
        Label(self.root, text="Capacidad").grid(row=8, column=0)
        self.entry_capacidad = Entry(self.root)
        self.entry_capacidad.grid(row=8, column=1)
        Button(self.root, text="Registrar Vuelo", command=self.registrar_vuelo).grid(row=9, columnspan=2)

        Label(self.root, text="Gestión de Asientos").grid(row=10, columnspan=3)
        Label(self.root, text="ID Vuelo:").grid(row=11, column=0)
        self.entry_id_vuelo = Entry(self.root)
        self.entry_id_vuelo.grid(row=11, column=1)
        Button(self.root, text="Mostrar Asientos Disponibles", command=self.mostrar_asientos).grid(row=11, column=2)

        self.listbox_asientos = Listbox(self.root, selectmode=SINGLE)
        self.listbox_asientos.grid(row=12, column=0, columnspan=3, sticky='we')

        Button(self.root, text="Reservar Asiento", command=self.reservar_asiento).grid(row=13, column=0)
        Button(self.root, text="Eliminar Asiento", command=self.eliminar_asiento).grid(row=13, column=1)
        Button(self.root, text="Salir", command=self.root.destroy).grid(row=13, column=2)

        self.root.mainloop()

    def registrar_pasajero(self):
        nombre = self.entry_nombre.get()
        pasaporte = self.entry_pasaporte.get()
        if not nombre or not pasaporte:
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        try:
            id_pasajero = registrar_pasajero(nombre, pasaporte)
            messagebox.showinfo("Éxito", f"Pasajero registrado con ID: {id_pasajero}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def registrar_vuelo(self):
        origen = self.entry_origen.get()
        destino = self.entry_destino.get()
        horario = self.entry_horario.get()
        try:
            capacidad = int(self.entry_capacidad.get())
        except ValueError:
            messagebox.showerror("Error", "Capacidad debe ser un número entero")
            return
        if not origen or not destino or not horario:
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        id_vuelo = registrar_vuelo(origen, destino, horario, capacidad)
        messagebox.showinfo("Éxito", f"Vuelo registrado con ID: {id_vuelo}")

    def mostrar_asientos(self):
        self.listbox_asientos.delete(0, END)
        try:
            id_vuelo = int(self.entry_id_vuelo.get())
        except ValueError:
            messagebox.showerror("Error", "ID de vuelo debe ser un número entero")
            return
        try:
            asientos = obtener_asientos_disponibles(id_vuelo)
            if not asientos:
                messagebox.showinfo("Información", "No hay asientos disponibles para este vuelo")
                return
            for asiento in asientos:
                self.listbox_asientos.insert(END, asiento)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reservar_asiento(self):
        idx = self.listbox_asientos.curselection()
        if not idx:
            messagebox.showwarning("Aviso", "Debe seleccionar un asiento para reservar")
            return
        asiento = self.listbox_asientos.get(idx[0])
        try:
            id_vuelo = int(self.entry_id_vuelo.get())
            id_pasajero = simpledialog.askstring("Pasajero", "Ingrese ID de pasajero para reservar boleto")
            if not id_pasajero or not id_pasajero.isdigit():
                messagebox.showerror("Error", "Debe ingresar un ID de pasajero válido")
                return
            id_pasajero = int(id_pasajero)
            id_boleto = vender_boleto(id_vuelo, id_pasajero, asiento)
            messagebox.showinfo("Éxito", f"Boleto vendido. Número: {id_boleto}")
            self.mostrar_asientos()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_asiento(self):
        idx = self.listbox_asientos.curselection()
        if not idx:
            messagebox.showwarning("Aviso", "Debe seleccionar un asiento para eliminar")
            return
        asiento = self.listbox_asientos.get(idx[0])
        try:
            id_vuelo = int(self.entry_id_vuelo.get())
            if eliminar_asiento(id_vuelo, asiento):
                messagebox.showinfo("Éxito", "Asiento eliminado correctamente")
                self.mostrar_asientos()
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    inicializar_bd()
    InterfazUsuario()
