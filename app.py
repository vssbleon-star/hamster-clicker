from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def game():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hamster Clicker 🐹</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background: #1a1a2e;
                color: white;
                text-align: center;
                padding: 20px;
                font-family: Arial;
                margin: 0;
                min-height: 100vh;
            }
            .hamster {
                width: 100px;
                height: 100px;
                background: gold;
                border-radius: 50%;
                margin: 30px auto;
                cursor: pointer;
                transition: transform 0.1s;
            }
            .hamster:active {
                transform: scale(0.9);
            }
            .coins {
                font-size: 40px;
                color: gold;
                font-weight: bold;
                margin: 20px;
            }
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 15px;
                margin: 10px;
                border-radius: 10px;
                font-size: 18px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>🐹 Hamster Clicker</h1>
        <div class="coins" id="coins">100</div>
        <div>Монеты 🪙</div>
        
        <div class="hamster" id="hamster" onclick="clickHamster()"></div>
        
        <button onclick="upgrade()">💪 Улучшить (50 🪙)</button>
        <button onclick="window.Telegram.WebApp.close()">❌ Закрыть</button>
        
        <script>
            let coins = 100;
            let power = 1;
            
            function clickHamster() {
                coins += power;
                document.getElementById('coins').textContent = coins;
                
                const hamster = document.getElementById('hamster');
                hamster.style.transform = 'scale(0.9)';
                setTimeout(() => hamster.style.transform = 'scale(1)', 100);
            }
            
            function upgrade() {
                const cost = 50;
                if (coins >= cost) {
                    coins -= cost;
                    power += 1;
                    document.getElementById('coins').textContent = coins;
                    alert('💪 Сила клика: ' + power);
                } else {
                    alert('Нужно ' + cost + ' монет!');
                }
            }
            
            // Telegram WebApp
            const tg = window.Telegram.WebApp;
            tg.expand();
            tg.ready();
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
