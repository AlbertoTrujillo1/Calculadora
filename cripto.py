import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
from colorama import Fore, Style, init
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from urllib.request import urlopen
from io import BytesIO

# Inicializamos colorama para colores de consola
init(autoreset=True)

# Lista de criptomonedas válidas
valid_cryptos = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOGE', 'LTC', 'MATIC', 'DOT', 'TRX', 'SHIB', 'AVAX', 'UNI']

# Función para obtener datos de Binance
def obtener_datos_binance(moneda, intervalo):
    url = f"https://api.binance.com/api/v3/klines?symbol={moneda}USDT&interval={intervalo}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"No se encontraron datos para {moneda} en el intervalo {intervalo}.")
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close'] = df['close'].astype(float)
        return df[['timestamp', 'close']]
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de Red", f"Error al obtener datos de Binance: {e}")
    except ValueError as ve:
        messagebox.showerror("Error de Datos", f"{ve}")
    return pd.DataFrame()

# Función para calcular la Media Móvil Simple (SMA)
def calcular_sma(df, periodo=20):
    if len(df) < periodo:
        return None
    df['SMA'] = df['close'].rolling(window=periodo).mean()

# Función para calcular el Índice de Fuerza Relativa (RSI)
def calcular_rsi(df, periodo=14):
    if len(df) < periodo:
        return None
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

# Función para calcular la cartera
def calcular_valor_cartera(df, cantidad_monedas):
    if df.empty:
        return 0
    precio_actual = df['close'].iloc[-1]
    valor_total = precio_actual * cantidad_monedas
    return valor_total

# Función para determinar si es un buen momento para comprar o vender
def evaluar_mercado(df):
    if df.empty:
        return "Datos insuficientes para análisis"

    rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else None
    sma = df['SMA'].iloc[-1] if 'SMA' in df.columns else None
    precio = df['close'].iloc[-1]

    if rsi is not None:
        if rsi > 70:
            return "Sobrecompra - Puede ser un buen momento para vender"
        elif rsi < 30:
            return "Sobreventa - Puede ser un buen momento para comprar"

    if sma is not None:
        if precio > sma:
            return "Alcista - Puede ser un buen momento para comprar"
        elif precio < sma:
            return "Bajista - Puede ser un buen momento para vender"

    return "Mercado neutral"

# Función para graficar los datos
def graficar_datos(df, mostrar_precio, mostrar_rsi, mostrar_sma):
    plt.clf()
    if mostrar_precio:
        plt.plot(df['timestamp'], df['close'], label='Precio de Cierre', color='royalblue', linewidth=2)
    if mostrar_sma and 'SMA' in df.columns:
        plt.plot(df['timestamp'], df['SMA'], label='SMA 20', color='orange', linewidth=2)
    plt.title("Gráfico de Precios y Media Móvil (SMA)", fontsize=14)
    plt.xlabel('Fecha', fontsize=12)
    plt.ylabel('Precio en USD', fontsize=12)
    plt.legend(loc='upper left', fontsize=12)

    if mostrar_rsi and 'RSI' in df.columns:
        plt.figure(figsize=(10, 3))
        plt.plot(df['timestamp'], df['RSI'], label='RSI', color='red', linewidth=2)
        plt.axhline(70, color='green', linestyle='--', label='Sobrecompra', linewidth=1)
        plt.axhline(30, color='green', linestyle='--', label='Sobreventa', linewidth=1)
        plt.title("Índice de Fuerza Relativa (RSI)", fontsize=14)
        plt.legend(loc='upper left', fontsize=12)

    canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Función que se ejecuta cuando el usuario presiona el botón de calcular
def calcular():
    try:
        moneda = combo_criptomoneda.get().upper()
        intervalo = combo_intervalo.get()
        cantidad_monedas = float(entry_cantidad.get())
        dinero_invertido = float(entry_invertido.get())
        fecha_venta = entry_fecha_venta.get()

        if moneda not in valid_cryptos:
            messagebox.showerror("Error", "Por favor, elige una criptomoneda válida.")
            return

        datos = obtener_datos_binance(moneda, intervalo)
        if datos.empty:
            return

        calcular_sma(datos)
        calcular_rsi(datos)

        valor_total = calcular_valor_cartera(datos, cantidad_monedas)

        resultado.config(text=f"El valor actual de tu cartera de {moneda} es: ${valor_total:.2f}", fg="#28A745")
        recomendacion = evaluar_mercado(datos)
        recomendacion_label.config(text=recomendacion, fg="#000000")

        mostrar_precio = var_precio.get()
        mostrar_rsi = var_rsi.get()
        mostrar_sma = var_sma.get()

        graficar_datos(datos, mostrar_precio, mostrar_rsi, mostrar_sma)
    except ValueError as ve:
        messagebox.showerror("Error de Entrada", f"Datos no válidos: {ve}")
    except Exception as e:
        messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}")

# Función principal para crear la interfaz gráfica
def main():
    global frame_grafico, combo_criptomoneda, combo_intervalo, entry_cantidad, entry_invertido, entry_fecha_venta, resultado, recomendacion_label
    global var_precio, var_rsi, var_sma

    ventana = tk.Tk()
    ventana.title("Calculadora de Criptomonedas")
    ventana.geometry("900x900")
    ventana.configure(bg="#FFFFFF")

    # Cargar y mostrar la imagen del logotipo
    try:
        img_url = "https://muntrumemotorsport.es/logo.webp"
        with urlopen(img_url) as u:
            raw_data = u.read()
        logo = Image.open(BytesIO(raw_data))
        logo = logo.resize((150, 150), Image.LANCZOS)
        logo_img = ImageTk.PhotoImage(logo)
        logo_label = tk.Label(ventana, image=logo_img, bg="#FFFFFF")
        logo_label.image = logo_img  # Referencia para evitar recolección de basura
        logo_label.pack(pady=10)
    except Exception as e:
        print(f"Error al cargar la imagen del logotipo: {e}")

    tk.Label(ventana, text="Calculadora de Criptomonedas", font=("Arial", 28, "bold"), fg="#28A745", bg="#FFFFFF").pack(pady=20)

    container = tk.Frame(ventana, bg="#FFFFFF")
    container.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    tk.Label(container, text="Selecciona la criptomoneda", font=("Arial", 14), bg="#FFFFFF", fg="#000000").grid(row=0, column=0, sticky=tk.W, pady=10)
    combo_criptomoneda = ttk.Combobox(container, values=valid_cryptos, state="readonly", font=("Arial", 12))
    combo_criptomoneda.grid(row=0, column=1, pady=10, padx=10)
    combo_criptomoneda.set(valid_cryptos[0])

    tk.Label(container, text="Selecciona el intervalo de tiempo", font=("Arial", 14), bg="#FFFFFF", fg="#000000").grid(row=1, column=0, sticky=tk.W, pady=10)
    combo_intervalo = ttk.Combobox(container, values=["1m", "5m", "1h", "1d"], state="readonly", font=("Arial", 12))
    combo_intervalo.grid(row=1, column=1, pady=10, padx=10)
    combo_intervalo.set("1d")

    tk.Label(container, text="Cantidad de monedas que posees", font=("Arial", 14), bg="#FFFFFF", fg="#000000").grid(row=2, column=0, sticky=tk.W, pady=10)
    entry_cantidad = tk.Entry(container, font=("Arial", 12))
    entry_cantidad.grid(row=2, column=1, pady=10, padx=10)

    tk.Label(container, text="Dinero invertido inicialmente (USD)", font=("Arial", 14), bg="#FFFFFF", fg="#000000").grid(row=3, column=0, sticky=tk.W, pady=10)
    entry_invertido = tk.Entry(container, font=("Arial", 12))
    entry_invertido.grid(row=3, column=1, pady=10, padx=10)

    tk.Label(container, text="Fecha de venta (YYYY-MM-DD)", font=("Arial", 14), bg="#FFFFFF", fg="#000000").grid(row=4, column=0, sticky=tk.W, pady=10)
    entry_fecha_venta = DateEntry(container, width=12, font=("Arial", 12), background='#28A745', foreground='white', borderwidth=2)
    entry_fecha_venta.grid(row=4, column=1, pady=10, padx=10)

    var_precio = tk.BooleanVar(value=True)
    var_rsi = tk.BooleanVar(value=True)
    var_sma = tk.BooleanVar(value=True)

    tk.Checkbutton(container, text="Mostrar Precio de Cierre", var=var_precio, bg="#FFFFFF", fg="#000000", selectcolor="#FFFFFF", font=("Arial", 12)).grid(row=5, column=0, sticky=tk.W, pady=5)
    tk.Checkbutton(container, text="Mostrar RSI", var=var_rsi, bg="#FFFFFF", fg="#000000", selectcolor="#FFFFFF", font=("Arial", 12)).grid(row=6, column=0, sticky=tk.W, pady=5)
    tk.Checkbutton(container, text="Mostrar SMA", var=var_sma, bg="#FFFFFF", fg="#000000", selectcolor="#FFFFFF", font=("Arial", 12)).grid(row=7, column=0, sticky=tk.W, pady=5)

    tk.Button(container, text="Calcular", font=("Arial", 14, "bold"), command=calcular, bg="#28A745", fg="#FFFFFF").grid(row=8, column=0, columnspan=2, pady=20)

    resultado = tk.Label(container, text="", font=("Arial", 14), fg="#000000", bg="#FFFFFF")
    resultado.grid(row=9, column=0, columnspan=2, pady=10)

    recomendacion_label = tk.Label(container, text="", font=("Arial", 14), fg="#000000", bg="#FFFFFF")
    recomendacion_label.grid(row=10, column=0, columnspan=2, pady=10)

    # Frame para los gráficos
    frame_grafico = tk.Frame(ventana, bg="#FFFFFF", relief=tk.RAISED, borderwidth=2)
    frame_grafico.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    # Pie de página
    footer = tk.Label(
        ventana,
        text="Desarrollado por [Tu Nombre]. Datos proporcionados por Binance.",
        font=("Arial", 10),
        bg="#FFFFFF",
        fg="#808080"
    )
    footer.pack(pady=10)

    ventana.mainloop()


if __name__ == "__main__":
    main()
