
import os
import time
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BINANCE = "https://api.binance.com/api/v3/ticker/price"
BYBIT = "https://api.bybit.com/v5/market/tickers"

running = False

def get_binance():
    data = requests.get(BINANCE, timeout=10).json()
    return {x["symbol"]: float(x["price"]) for x in data}

def get_bybit():
    data = requests.get(
        BYBIT,
        params={"category": "spot"},
        timeout=10
    ).json()
    return {
        x["symbol"]: float(x["lastPrice"])
        for x in data["result"]["list"]
    }

def send(message):
    if TOKEN and CHAT_ID:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )

def scan():
    a = get_binance()
    b = get_bybit()
    results = []

    for symbol in a.keys() & b.keys():
        if a[symbol] <= 0 or b[symbol] <= 0:
            continue

        difference = (b[symbol] - a[symbol]) / a[symbol] * 100

        if abs(difference) >= 0.5:
            results.append(
                f"{symbol}: Binance {a[symbol]} | "
                f"Bybit {b[symbol]} | Різниця {difference:.2f}%"
            )

    return results[:15]

def main():
    global running
    offset = None

    send("Сканер Binance + Bybit запущено!")

    while True:
        try:
            updates = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 20},
                timeout=25
            ).json()

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat = str(msg.get("chat", {}).get("id", ""))

                if chat != str(CHAT_ID):
                    continue

                if text == "/start":
                    send("Бот працює!\n/scan — перевірити ціни\n/alerts — увімкнути сигнали\n/stop — вимкнути сигнали")

                elif text == "/scan":
                    results = scan()
                    send("\n".join(results) if results else "Вигідних різниць не знайдено.")

                elif text == "/alerts":
                    running = True
                    send("Автоматичні сповіщення увімкнено.")

                elif text == "/stop":
                    running = False
                    send("Сповіщення вимкнено.")

            if running:
                results = scan()
                if results:
                    send("Арбітражні сигнали:\n" + "\n".join(results))
                time.sleep(30)

        except Exception as e:
            print("Помилка:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
