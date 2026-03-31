import tkinter as tk
import requests
import threading
import time
import yfinance as yf

# စောင့်ကြည့်မည့် Asset များ
COINS = ['BTC', 'BNB', 'ETH', 'PAXG', 'ASTER']
SYMBOLS = {coin: f"{coin}USDT" for coin in COINS}

class MarketResizableFloater:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Market Monitor")
        
        # Window Settings
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True) 
        self.root.attributes('-alpha', 0.85) 
        
        # Initial Window Size
        self.root.geometry("350x300+100+100")
        self.root.config(bg='#121212') 

        # Resizing အတွက် လိုအပ်သော variables များ
        self._resizing = False
        self.labels = {}
        self.last_prices = {asset: 0.0 for asset in COINS + ['OIL']}

        # Main Container (Grid layout ကို flexible ဖြစ်အောင် လုပ်ထားသည်)
        self.container = tk.Frame(self.root, bg='#121212')
        self.container.pack(fill="both", expand=True)

        for i in range(3): self.container.rowconfigure(i, weight=1)
        for i in range(2): self.container.columnconfigure(i, weight=1)

        all_assets = COINS + ['OIL']
        for i, asset in enumerate(all_assets):
            frame = tk.Frame(self.container, bg='#121212')
            frame.grid(row=i//2, column=i%2, sticky="nsew", padx=5, pady=5)
            
            title_color = "#FFD700" if asset == 'ASTER' else "#AAAAAA"
            display_name = "BRENT OIL" if asset == 'OIL' else asset
            
            name_label = tk.Label(frame, text=display_name, font=("Arial", 10, "bold"), fg=title_color, bg='#121212')
            name_label.pack(expand=True)
            
            price_label = tk.Label(frame, text="...", font=("Consolas", 12, "bold"), fg="white", bg='#121212')
            price_label.pack(expand=True)
            
            self.labels[asset] = price_label
            
            # Dragging & Closing Interactions
            for widget in [frame, name_label, price_label]:
                widget.bind("<Button-1>", self.start_move)
                widget.bind("<B1-Motion>", self.do_move)
                widget.bind("<Button-3>", lambda e: self.root.destroy())

        # --- RESIZE GRIP (ညာဘက်အောက်ခြေတွင် ချဲ့ရန်နေရာ ပြုလုပ်ခြင်း) ---
        self.grip = tk.Label(self.root, bg='#333333', cursor="size_nw_se")
        self.grip.place(relx=1.0, rely=1.0, anchor="se", width=15, height=15)
        self.grip.bind("<Button-1>", self.init_resize)
        self.grip.bind("<B1-Motion>", self.push_resize)

        self.update_thread = threading.Thread(target=self.refresh_data, daemon=True)
        self.update_thread.start()

    # Move logic
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        self.root.geometry(f"+{self.root.winfo_x() + deltax}+{self.root.winfo_y() + deltay}")

    # Resize logic
    def init_resize(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.start_width = self.root.winfo_width()
        self.start_height = self.root.winfo_height()

    def push_resize(self, event):
        new_width = max(200, self.start_width + (event.x_root - self.start_x))
        new_height = max(150, self.start_height + (event.y_root - self.start_y))
        self.root.geometry(f"{new_width}x{new_height}")

    def get_binance_prices(self):
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            response = requests.get(url, timeout=5)
            all_prices = response.json()
            return {item['symbol']: float(item['price']) for item in all_prices if item['symbol'] in SYMBOLS.values()}
        except: return None

    def get_oil_price(self):
        try:
            oil = yf.Ticker("BZ=F")
            data = oil.history(period="1d")
            return float(data['Close'].iloc[-1]) if not data.empty else None
        except: return None

    def format_price(self, asset, price):
        if price is None: return "N/A"
        if price < 1: return f"${price:.4f}"
        if price < 100: return f"${price:.2f}"
        if price < 10000: return f"${price:.1f}"
        return f"${int(price):,}"

    def update_label(self, asset, price):
        if price:
            color = "#00FF00" if price > self.last_prices[asset] else "#FF4444" if price < self.last_prices[asset] else "#FFFFFF"
            self.last_prices[asset] = price
            self.labels[asset].config(text=self.format_price(asset, price), fg=color)

    def refresh_data(self):
        while True:
            crypto_data = self.get_binance_prices()
            if crypto_data:
                for coin in COINS: self.update_label(coin, crypto_data.get(SYMBOLS[coin]))
            oil_p = self.get_oil_price()
            if oil_p: self.update_label('OIL', oil_p)
            time.sleep(5)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MarketResizableFloater()
    app.run()