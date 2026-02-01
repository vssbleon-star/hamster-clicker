from flask import Flask, jsonify, request, send_from_directory, render_template_string
import os
import time
from datetime import datetime
import sqlite3
import threading

app = Flask(__name__, static_folder='static')

# ================= НАСТРОЙКА ПУТЕЙ =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DB_FILE = os.path.join(BASE_DIR, 'hamster.db')

# Создаём папки если их нет
os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'images'), exist_ok=True)

# ================= БАЗА ДАННЫХ SQLite =================
def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        coins INTEGER DEFAULT 100,
        power INTEGER DEFAULT 1,
        autos INTEGER DEFAULT 0,
        multiplier INTEGER DEFAULT 1,
        total_clicks INTEGER DEFAULT 0,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица лидерборда
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        coins INTEGER,
        power INTEGER,
        rank INTEGER,
        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица достижений
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        user_id TEXT,
        achievement_id TEXT,
        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, achievement_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Инициализация БД при старте
init_db()

def get_db():
    """Получение соединения с БД"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ================= СТАТИЧЕСКИЕ ФАЙЛЫ =================
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Отдача статических файлов"""
    return send_from_directory(STATIC_DIR, filename)

# ================= HTML ИГРА =================
HTML_GAME = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐹 Hamster Empire</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* Дополнительные стили будут загружены из CSS */
    </style>
</head>
<body>
    <div class="container">
        <!-- Шапка -->
        <div class="header">
            <h1><i class="fas fa-paw"></i> HAMSTER EMPIRE</h1>
            <div class="online-count">
                <i class="fas fa-users"></i> <span id="onlineCount">1</span> онлайн
            </div>
        </div>
        
        <!-- Статистика -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="coins">100</div>
                <div class="stat-label"><i class="fas fa-coins"></i> МОНЕТЫ</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="power">1</div>
                <div class="stat-label"><i class="fas fa-bolt"></i> СИЛА</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="autos">0</div>
                <div class="stat-label"><i class="fas fa-robot"></i> АВТО</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="multiplier">1x</div>
                <div class="stat-label"><i class="fas fa-rocket"></i> БУСТ</div>
            </div>
        </div>
        
        <!-- Хомяк -->
        <div class="hamster-section">
            <div class="hamster-container" id="hamsterBtn">
                <div class="hamster">
                    <!-- Если есть изображение хомяка -->
                    <img src="/static/images/hamster.png" alt="Хомяк" 
                         style="width: 100%; height: 100%; border-radius: 50%; display: none;" 
                         id="hamsterImage">
                    <div class="face" id="hamsterFace">
                        <div class="eye eye-left"></div>
                        <div class="eye eye-right"></div>
                        <div class="nose"></div>
                        <div class="cheek cheek-left"></div>
                        <div class="cheek cheek-right"></div>
                    </div>
                </div>
            </div>
            <div style="margin-top: 15px; font-size: 0.9rem; opacity: 0.8;">
                <i class="fas fa-mouse-pointer"></i> Кликай на хомяка для сбора монет!
            </div>
        </div>
        
        <!-- Кнопки действий -->
        <div class="buttons-grid">
            <button class="btn upgrade" onclick="buyUpgrade()">
                <i class="fas fa-bolt"></i> Улучшить
                <div class="btn-cost"><span id="upgradeCost">50</span> <i class="fas fa-coins"></i></div>
            </button>
            <button class="btn auto" onclick="buyAuto()">
                <i class="fas fa-robot"></i> Авто-кликер
                <div class="btn-cost"><span id="autoCost">100</span> <i class="fas fa-coins"></i></div>
            </button>
            <button class="btn" onclick="buyMultiplier()">
                <i class="fas fa-rocket"></i> Буст x2
                <div class="btn-cost"><span id="multiplierCost">500</span> <i class="fas fa-coins"></i></div>
            </button>
            <button class="btn" onclick="showTab('leaderboard')">
                <i class="fas fa-trophy"></i> Лидерборд
            </button>
        </div>
        
        <!-- Подключение JavaScript -->
        <script src="/static/js/game.js"></script>
        <script>
            // Упрощенная версия игры
            const game = {
                coins: 100,
                power: 1,
                autos: 0,
                multiplier: 1,
                totalClicks: 0,
                
                init() {
                    this.loadGame();
                    this.setupEventListeners();
                    this.startAutoClickers();
                    this.updateDisplay();
                    
                    // Проверяем изображение
                    const hamsterImg = document.getElementById('hamsterImage');
                    if (hamsterImg) {
                        hamsterImg.onerror = () => {
                            console.log('Изображение не загружено, показываем лицо хомяка');
                        };
                    }
                },
                
                loadGame() {
                    const saved = localStorage.getItem('hamster_save');
                    if (saved) {
                        const data = JSON.parse(saved);
                        Object.assign(this, data);
                    }
                },
                
                saveGame() {
                    localStorage.setItem('hamster_save', JSON.stringify({
                        coins: this.coins,
                        power: this.power,
                        autos: this.autos,
                        multiplier: this.multiplier,
                        totalClicks: this.totalClicks
                    }));
                },
                
                clickHamster() {
                    const earned = this.power * this.multiplier;
                    this.coins += earned;
                    this.totalClicks++;
                    
                    // Анимация
                    const hamster = document.getElementById('hamsterBtn');
                    if (hamster) {
                        hamster.style.transform = 'scale(0.95)';
                        setTimeout(() => hamster.style.transform = 'scale(1)', 100);
                    }
                    
                    this.updateDisplay();
                    this.saveGame();
                    
                    // Эффект
                    this.createEffect(`+${earned} 🪙`, '#f59e0b');
                },
                
                buyUpgrade() {
                    const cost = 50 * this.power;
                    if (this.coins >= cost) {
                        this.coins -= cost;
                        this.power += 1;
                        this.updateDisplay();
                        this.saveGame();
                        this.createEffect('💪 Сила +1', '#2ecc71');
                        return true;
                    }
                    this.createEffect(`❌ Нужно ${cost} монет!`, '#e74c3c');
                    return false;
                },
                
                buyAuto() {
                    const cost = 100 + (this.autos * 50);
                    if (this.coins >= cost) {
                        this.coins -= cost;
                        this.autos += 1;
                        this.updateDisplay();
                        this.saveGame();
                        this.createEffect('🤖 Авто-кликер +1', '#9b59b6');
                        return true;
                    }
                    this.createEffect(`❌ Нужно ${cost} монет!`, '#e74c3c');
                    return false;
                },
                
                updateDisplay() {
                    document.getElementById('coins').textContent = this.coins;
                    document.getElementById('power').textContent = this.power;
                    document.getElementById('autos').textContent = this.autos;
                    document.getElementById('multiplier').textContent = this.multiplier + 'x';
                    document.getElementById('upgradeCost').textContent = 50 * this.power;
                    document.getElementById('autoCost').textContent = 100 + (this.autos * 50);
                },
                
                createEffect(text, color) {
                    const effect = document.createElement('div');
                    effect.textContent = text;
                    effect.style.cssText = `
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        color: ${color};
                        font-weight: bold;
                        font-size: 24px;
                        z-index: 1000;
                        pointer-events: none;
                        animation: floatUp 1s forwards;
                    `;
                    
                    document.body.appendChild(effect);
                    setTimeout(() => effect.remove(), 1000);
                },
                
                setupEventListeners() {
                    const hamster = document.getElementById('hamsterBtn');
                    if (hamster) {
                        hamster.addEventListener('click', (e) => {
                            this.clickHamster();
                        });
                    }
                    
                    // Кнопки улучшений
                    document.querySelector('.btn.upgrade')?.addEventListener('click', () => this.buyUpgrade());
                    document.querySelector('.btn.auto')?.addEventListener('click', () => this.buyAuto());
                },
                
                startAutoClickers() {
                    setInterval(() => {
                        if (this.autos > 0) {
                            const earned = this.autos * this.multiplier;
                            this.coins += earned;
                            this.updateDisplay();
                            this.saveGame();
                        }
                    }, 3000);
                }
            };
            
            // Инициализация при загрузке
            document.addEventListener('DOMContentLoaded', () => {
                game.init();
                
                // Добавляем анимации
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes floatUp {
                        0% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                        100% { opacity: 0; transform: translate(-50%, -100px) scale(1.5); }
                    }
                `;
                document.head.appendChild(style);
            });
            
            // Глобальные функции
            window.buyUpgrade = () => game.buyUpgrade();
            window.buyAuto = () => game.buyAuto();
            window.buyMultiplier = () => alert('Функция в разработке!');
            window.showTab = () => alert('Вкладки в разработке!');
        </script>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_GAME

# ================= API ЭНДПОИНТЫ =================
@app.route('/api/save', methods=['POST'])
def save_progress():
    """Сохранить прогресс игрока"""
    try:
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username', 'Игрок')
        
        if not user_id:
            return jsonify({'error': 'No user_id'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Обновляем или создаем пользователя
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, coins, power, autos, multiplier, total_clicks, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            user_id,
            username,
            data.get('coins', 100),
            data.get('power', 1),
            data.get('autos', 0),
            data.get('multiplier', 1),
            data.get('total_clicks', 0)
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Получить лидерборд"""
    try:
        conn = get_db()
        
        # Получаем топ игроков
        leaderboard = conn.execute('''
            SELECT user_id, username, coins, power 
            FROM users 
            ORDER BY coins DESC 
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leaderboard': [dict(row) for row in leaderboard]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Проверка здоровья
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Hamster Empire запущен на порту {port}")
    print(f"📁 Статика в папке: {STATIC_DIR}")
    print(f"🗄️  База данных: {DB_FILE}")
    app.run(host='0.0.0.0', port=port, debug=True)
