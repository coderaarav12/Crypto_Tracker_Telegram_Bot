import urllib.request
import json
import time
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_crypto_data():
    try:
        # Fetch data from CoinGecko API
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,dogecoin&vs_currencies=usd&include_24hr_change=true"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        return data
    except Exception as e:
        return None

def display_dashboard():
    while True:
        clear_screen()
        print("==================================================")
        print(" [REAL-TIME CRYPTO TRACKER (TECH CLUB PITCH)] ")
        print("==================================================")
        
        print("\n[*] Fetching live market data...\n")
        data = get_crypto_data()
        
        if data:
            for coin, info in data.items():
                price = info['usd']
                change = info['usd_24h_change']
                
                # Format the output with basic terminal colors
                color = "\033[92m+" if change >= 0 else "\033[91m"
                reset = "\033[0m"
                
                print(f" [*]  {coin.capitalize():<10} | ${price:,.2f} | {color}{change:.2f}%{reset}")
        else:
            print("[!] Error fetching data. Please check your internet connection.")
            
        print("\n==================================================")
        print("[*] Auto-updating every 10 seconds. Press Ctrl+C to exit.")
        time.sleep(10)

if __name__ == "__main__":
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\n[*] Exiting tracker. Have a great pitch!")
