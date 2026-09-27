import os
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from flask import Flask, jsonify, request
import yfinance as yf

app = Flask(__name__, static_folder='static', static_url_path='/static')
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# Set a beautiful dark theme for charts
plt.style.use('dark_background')

@app.route('/api/price/<coin>', methods=['GET'])
def get_price(coin):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return jsonify({'error': 'Not found'}), 404
        c = data[0]
        return jsonify({
            'name': c.get('name'),
            'symbol': c.get('symbol', '').upper(),
            'price': c.get('current_price'),
            'usd_24h_change': c.get('price_change_percentage_24h'),
            'market_cap': c.get('market_cap'),
            'market_cap_rank': c.get('market_cap_rank'),
            'total_volume': c.get('total_volume'),
            'high_24h': c.get('high_24h'),
            'low_24h': c.get('low_24h'),
            'circulating_supply': c.get('circulating_supply'),
            'total_supply': c.get('total_supply'),
            'ath': c.get('ath'),
            'ath_change_percentage': c.get('ath_change_percentage')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart/<coin>', methods=['GET'])
def get_chart(coin):
    try:
        days = request.args.get('days', '7')
        url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days={days}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices = data.get('prices', [])
        if not prices:
            return jsonify({'error': 'No data'}), 404
            
        timestamps = [datetime.fromtimestamp(p[0]/1000.0) for p in prices]
        values = [p[1] for p in prices]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#121212')
        ax.set_facecolor('#121212')
        ax.plot(timestamps, values, color='#00ffcc', linewidth=2)
        
        # Beautify
        ax.set_title(f'{coin.capitalize()} {days}-Day Market Trend', color='white', fontsize=16, pad=15)
        ax.set_ylabel('Price (USD)', color='white')
        ax.tick_params(colors='white')
        
        # Format x-axis as dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.xticks(rotation=45, color='white')
        plt.yticks(color='white')
        
        ax.grid(color='#333333', linestyle='--', linewidth=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('white')
        ax.spines['bottom'].set_color('white')
        
        plt.tight_layout()
        
        filename = f"chart_{coin}_{days}d.png"
        filepath = os.path.join(STATIC_DIR, filename)
        plt.savefig(filepath, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close()
        
        return jsonify({'chart_url': f'/static/{filename}', 'chart_path': filepath})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/info/<coin>', methods=['GET'])
def get_info(coin):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin}?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        desc = data.get('description', {}).get('en', '')
        link = data.get('links', {}).get('homepage', [''])[0]
        return jsonify({'description': desc, 'homepage': link})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<query>', methods=['GET'])
def get_stock(query):
    try:
        # Search for ticker
        search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(search_url, headers=headers, timeout=10)
        search_data = res.json()
        
        quotes = search_data.get('quotes', [])
        if not quotes:
            return jsonify({'error': 'Stock not found'}), 404
            
        ticker = quotes[0]['symbol']
        name = quotes[0].get('shortname', ticker)
        
        stock = yf.Ticker(ticker)
        history = stock.history(period="2d")
        if history.empty:
            return jsonify({'error': 'No price data'}), 404
            
        current_price = history['Close'].iloc[-1]
        prev_price = history['Close'].iloc[0] if len(history) > 1 else current_price
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        info = stock.info
        market_cap = info.get('marketCap')
        day_high = info.get('dayHigh')
        day_low = info.get('dayLow')
        vol = info.get('volume')
        f52_high = info.get('fiftyTwoWeekHigh')
        
        return jsonify({
            'name': name,
            'symbol': ticker,
            'price': current_price,
            'change_pct': change_pct,
            'market_cap': market_cap,
            'day_high': day_high,
            'day_low': day_low,
            'volume': vol,
            'fiftyTwoWeekHigh': f52_high
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news/<query>', methods=['GET'])
def get_news(query):
    try:
        # Search for ticker
        search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(search_url, headers=headers, timeout=10)
        search_data = res.json()
        
        quotes = search_data.get('quotes', [])
        if not quotes:
            return jsonify({'error': 'Not found'}), 404
            
        ticker = quotes[0]['symbol']
        stock = yf.Ticker(ticker)
        
        news_items = stock.news[:3] # Get top 3 news
        results = []
        for n in news_items:
            content = n.get('content', {})
            title = content.get('title', 'Headline')
            ct_url = content.get('clickThroughUrl') or {}
            link = ct_url.get('url', '#')
            if link == '#' and content.get('canonicalUrl'):
                link = (content.get('canonicalUrl') or {}).get('url', '#')
            results.append({
                'title': title,
                'link': link
            })
            
        return jsonify({'news': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trending', methods=['GET'])
def get_trending():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_crypto/<query>', methods=['GET'])
def search_crypto(query):
    try:
        url = f"https://api.coingecko.com/api/v3/search?query={query}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        coins = data.get('coins', [])
        if not coins:
            return jsonify({'error': 'Not found'}), 404
        return jsonify({'id': coins[0]['id'], 'name': coins[0]['name'], 'symbol': coins[0]['symbol']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top10', methods=['GET'])
def get_top10():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return jsonify({'top10': response.json()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/general_news', methods=['GET'])
def get_general_news():
    try:
        stock = yf.Ticker('^GSPC') # S&P 500 for general market news
        news_items = stock.news[:5]
        results = []
        for n in news_items:
            content = n.get('content', {})
            title = content.get('title', 'Headline')
            ct_url = content.get('clickThroughUrl') or {}
            link = ct_url.get('url', '#')
            if link == '#' and content.get('canonicalUrl'):
                link = (content.get('canonicalUrl') or {}).get('url', '#')
            results.append({
                'title': title,
                'link': link
            })
        return jsonify({'news': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fear_greed', methods=['GET'])
def get_fear_greed():
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return jsonify(data['data'][0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5003)
