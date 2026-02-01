from flask import Flask, request, jsonify, render_template_string
import json
import os
import time
from datetime import datetime
from flask_cors import CORS
import sqlite3
import threading

app = Flask(__name__)
CORS(app)

# ================= БАЗА ДАННЫХ =================
DB_FILE = 'hamster_db.sqlite'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        coins BIGINT DEFAULT 100,
        power INTEGER DEFAULT 1,
        autos INTEGER DEFAULT 0,
        multiplier INTEGER DEFAULT 1,
        total_clicks INTEGER DEFAULT 0,
        achievements TEXT DEFAULT '[]',
        last_active TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица транзакций (для статистики)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        type TEXT,
        amount INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица лидерборда (кешированный)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard_cache (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        coins BIGINT,
        power INTEGER,
        rank INTEGER,
        last_update TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Инициализация БД при старте
init_db()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ================= HTML ШАБЛОН =================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐹 HAMSTER EMPIRE - Ultimate Clicker</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #8b5cf6;
            --accent: #f59e0b;
            --success: #10b981;
            --danger: #ef4444;
            --dark: #1e293b;
            --darker: #0f172a;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            user-select: none;
        }
        
        body {
            background: linear-gradient(135deg, var(--darker), var(--dark));
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        
        /* Фоновые частицы */
        #particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }
        
        /* Шапка */
        .header {
            text-align: center;
            margin-bottom: 25px;
            position: relative;
        }
        
        .header h1 {
            font-size: 2.8rem;
            background: linear-gradient(45deg, var(--accent), #fbbf24);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            text-shadow: 0 2px 20px rgba(245, 158, 11, 0.3);
        }
        
        .online-count {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 8px 16px;
            display: inline-block;
            font-size: 0.9rem;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        /* Статистика */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            backdrop-filter: blur(15px);
            border-radius: 16px;
            padding: 18px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.15);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transition: 0.5s;
        }
        
        .stat-card:hover::before {
            left: 100%;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 800;
            color: var(--accent);
            margin-bottom: 5px;
            text-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
        }
        
        .stat-label {
            font-size: 0.8rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Хомяк */
        .hamster-section {
            position: relative;
            margin: 30px 0;
            text-align: center;
        }
        
        .hamster-container {
            position: relative;
            display: inline-block;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .hamster {
            width: 180px;
            height: 180px;
            background: linear-gradient(145deg, var(--accent), #fbbf24);
            border-radius: 50%;
            position: relative;
            box-shadow: 
                0 20px 40px rgba(245, 158, 11, 0.4),
                inset 0 -10px 20px rgba(0,0,0,0.2),
                inset 0 10px 20px rgba(255,255,255,0.3);
            animation: float 3s ease-in-out infinite;
            overflow: hidden;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-10px) rotate(5deg); }
        }
        
        .hamster:active {
            animation: click 0.2s;
            box-shadow: 
                0 10px 20px rgba(245, 158, 11, 0.6),
                inset 0 -5px 10px rgba(0,0,0,0.3),
                inset 0 5px 10px rgba(255,255,255,0.4);
        }
        
        @keyframes click {
            0% { transform: scale(1); }
            50% { transform: scale(0.95); }
            100% { transform: scale(1); }
        }
        
        /* Лицо хомяка */
        .face {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 120px;
        }
        
        .eye {
            width: 24px;
            height: 24px;
            background: #1e293b;
            border-radius: 50%;
            position: absolute;
            top: 35px;
            animation: blink 3s infinite;
        }
        
        @keyframes blink {
            0%, 45%, 55%, 100% { height: 24px; }
            50% { height: 4px; }
        }
        
        .eye.left { left: 28px; }
        .eye.right { right: 28px; }
        
        .nose {
            width: 20px;
            height: 16px;
            background: #dc2626;
            border-radius: 50%;
            position: absolute;
            top: 65px;
            left: 50%;
            transform: translateX(-50%);
        }
        
        .cheek {
            width: 30px;
            height: 15px;
            background: rgba(220, 38, 38, 0.3);
            border-radius: 50%;
            position: absolute;
            top: 75px;
        }
        
        .cheek.left { left: 15px; }
        .cheek.right { right: 15px; }
        
        /* Кнопки */
        .buttons-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin: 25px 0;
        }
        
        .btn {
            background: linear-gradient(145deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            padding: 18px;
            border-radius: 14px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .btn:active::before {
            width: 300px;
            height: 300px;
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        }
        
        .btn.upgrade { background: linear-gradient(145deg, var(--success), #059669); }
        .btn.auto { background: linear-gradient(145deg, #8b5cf6, #7c3aed); }
        .btn.boost { background: linear-gradient(145deg, #f59e0b, #d97706); }
        .btn.prestige { background: linear-gradient(145deg, #ec4899, #db2777); }
        
        .btn-cost {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 5px;
        }
        
        /* Вкладки */
        .tabs-container {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            margin-top: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            overflow: hidden;
        }
        
        .tabs-header {
            display: flex;
            background: rgba(0,0,0,0.3);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .tab-btn {
            flex: 1;
            padding: 18px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            position: relative;
        }
        
        .tab-btn.active {
            background: var(--primary);
            color: white;
        }
        
        .tab-btn::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            width: 0;
            height: 3px;
            background: var(--accent);
            transition: all 0.3s;
            transform: translateX(-50%);
        }
        
        .tab-btn.active::after {
            width: 80%;
        }
        
        .tab-content {
            padding: 25px;
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.5s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Лидерборд */
        .leaderboard {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .leaderboard-item {
            display: flex;
            align-items: center;
            padding: 15px;
            margin: 8px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            transition: all 0.3s;
        }
        
        .leaderboard-item:hover {
            background: rgba(255,255,255,0.1);
            transform: translateX(5px);
        }
        
        .rank {
            width: 36px;
            height: 36px;
            background: linear-gradient(145deg, var(--accent), #f59e0b);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            margin-right: 15px;
            color: var(--darker);
        }
        
        .rank-1 { background: linear-gradient(145deg, #fbbf24, #f59e0b); }
        .rank-2 { background: linear-gradient(145deg, #94a3b8, #64748b); }
        .rank-3 { background: linear-gradient(145deg, #a16207, #854d0e); }
        
        .user-info {
            flex: 1;
        }
        
        .user-name {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .user-stats {
            font-size: 0.9rem;
            opacity: 0.8;
            display: flex;
            gap: 15px;
        }
        
        /* Магазин */
        .shop-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        
        .shop-item {
            background: rgba(255,255,255,0.05);
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s;
            border: 1px solid transparent;
        }
        
        .shop-item:hover {
            border-color: var(--primary);
            transform: translateY(-5px);
        }
        
        .shop-icon {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .shop-title {
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .shop-desc {
            font-size: 0.85rem;
            opacity: 0.8;
            margin-bottom: 12px;
            min-height: 40px;
        }
        
        /* Прогресс-бары */
        .progress-bar {
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            margin: 15px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--success), var(--accent));
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        
        /* Уведомления */
        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(145deg, var(--primary), var(--secondary));
            color: white;
            padding: 15px 25px;
            border-radius: 12px;
            z-index: 1000;
            animation: slideDown 0.3s ease-out;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 90%;
        }
        
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-50px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
        
        /* Адаптивность */
        @media (max-width: 600px) {
            .container { padding: 15px; }
            .header h1 { font-size: 2.2rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .buttons-grid { grid-template-columns: 1fr; }
            .shop-grid { grid-template-columns: 1fr; }
            .hamster { width: 150px; height: 150px; }
        }
    </style>
</head>
<body>
    <div id="particles"></div>
    
    <div class="container">
        <!-- Шапка -->
        <div class="header">
            <h1>🐹 HAMSTER EMPIRE</h1>
            <div class="online-count">
                🟢 <span id="onlineCount">1</span> игроков онлайн
            </div>
        </div>
        
        <!-- Статистика -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="coins">0</div>
                <div class="stat-label">МОНЕТЫ</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="power">1</div>
                <div class="stat-label">СИЛА</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="autos">0</div>
                <div class="stat-label">АВТО-КЛИКЕРЫ</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="multiplier">1x</div>
                <div class="stat-label">МНОЖИТЕЛЬ</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="totalClicks">0</div>
                <div class="stat-label">ВСЕГО КЛИКОВ</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="incomePerSec">0</div>
                <div class="stat-label">В СЕКУНДУ</div>
            </div>
        </div>
        
        <!-- Хомяк -->
        <div class="hamster-section">
            <div class="hamster-container" id="hamsterBtn">
                <div class="hamster">
                    <div class="face">
                        <div class="eye left"></div>
                        <div class="eye right"></div>
                        <div class="nose"></div>
                        <div class="cheek left"></div>
                        <div class="cheek right"></div>
                    </div>
                </div>
            </div>
            <div style="margin-top: 15px; font-size: 0.9rem; opacity: 0.8;">
                🎯 Нажми на хомяка для сбора монет!
            </div>
        </div>
        
        <!-- Кнопки действий -->
        <div class="buttons-grid">
            <button class="btn upgrade" onclick="buyUpgrade()">
                ⚡ Улучшить
                <div class="btn-cost"><span id="upgradeCost">50</span> 🪙</div>
            </button>
            <button class="btn auto" onclick="buyAutoClicker()">
                🤖 Авто-кликер
                <div class="btn-cost"><span id="autoCost">100</span> 🪙</div>
            </button>
            <button class="btn boost" onclick="buyMultiplier()">
                🚀 Буст x2
                <div class="btn-cost"><span id="multiplierCost">500</span> 🪙</div>
            </button>
            <button class="btn prestige" onclick="showPrestige()">
                👑 Престиж
                <div class="btn-cost">10,000 🪙</div>
            </button>
        </div>
        
        <!-- Вкладки -->
        <div class="tabs-container">
            <div class="tabs-header">
                <div class="tab-btn active" onclick="showTab('shop')">🛒 Магазин</div>
                <div class="tab-btn" onclick="showTab('leaderboard')">🏆 Лидерборд</div>
                <div class="tab-btn" onclick="showTab('achievements')">⭐ Достижения</div>
                <div class="tab-btn" onclick="showTab('stats')">📊 Статистика</div>
            </div>
            
            <!-- Магазин -->
            <div class="tab-content active" id="shopTab">
                <div class="shop-grid">
                    <!-- Улучшения будут добавлены через JS -->
                </div>
            </div>
            
            <!-- Лидерборд -->
            <div class="tab-content" id="leaderboardTab">
                <div class="leaderboard" id="leaderboardList">
                    <!-- Лидерборд загрузится здесь -->
                </div>
            </div>
            
            <!-- Достижения -->
            <div class="tab-content" id="achievementsTab">
                <div id="achievementsList">
                    <!-- Достижения загрузятся здесь -->
                </div>
            </div>
            
            <!-- Статистика -->
            <div class="tab-content" id="statsTab">
                <div id="statsContent">
                    <!-- Статистика загрузится здесь -->
                </div>
            </div>
        </div>
        
        <!-- Прогресс -->
        <div style="margin-top: 25px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span>Прогресс до следующего уровня</span>
                <span id="levelProgress">0/100</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill" style="width: 0%"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Полный JavaScript код с улучшениями
        // (ограничение символов, продолжу в следующем сообщении)
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_TEMPLATE

# API эндпоинты
@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return jsonify(dict(user))
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/save', methods=['POST'])
def save_progress():
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username')
    
    if not user_id:
        return jsonify({'error': 'No user_id'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем существующего пользователя
    user = cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    if user:
        # Обновляем существующего
        cursor.execute('''
            UPDATE users SET 
                coins = ?, power = ?, autos = ?, multiplier = ?,
                total_clicks = ?, achievements = ?, last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            data.get('coins', user['coins']),
            data.get('power', user['power']),
            data.get('autos', user['autos']),
            data.get('multiplier', user['multiplier']),
            data.get('total_clicks', user['total_clicks']),
            json.dumps(data.get('achievements', json.loads(user['achievements']))),
            user_id
        ))
    else:
        # Создаем нового
        cursor.execute('''
            INSERT INTO users 
            (user_id, username, coins, power, autos, multiplier, total_clicks, achievements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            username or 'Игрок',
            data.get('coins', 100),
            data.get('power', 1),
            data.get('autos', 0),
            data.get('multiplier', 1),
            data.get('total_clicks', 0),
            json.dumps(data.get('achievements', []))
        ))
    
    conn.commit()
    
    # Обновляем кеш лидерборда
    update_leaderboard_cache(conn, user_id)
    
    conn.close()
    return jsonify({'success': True})

@app.route('/api/leaderboard')
def get_leaderboard():
    conn = get_db()
    leaderboard = conn.execute('''
        SELECT user_id, username, coins, power, rank
        FROM leaderboard_cache 
        ORDER BY coins DESC 
        LIMIT 50
    ''').fetchall()
    
    # Считаем онлайн игроков (активны последние 5 минут)
    online = conn.execute('''
        SELECT COUNT(*) as count FROM users 
        WHERE last_active > datetime('now', '-5 minutes')
    ''').fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'leaderboard': [dict(row) for row in leaderboard],
        'online': online,
        'timestamp': datetime.now().isoformat()
    })

def update_leaderboard_cache(conn, user_id=None):
    # Обновляем весь лидерборд или конкретного пользователя
    if user_id:
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if user:
            # Считаем ранг
            rank = conn.execute('''
                SELECT COUNT(*) + 1 as rank FROM users 
                WHERE coins > ?
            ''', (user['coins'],)).fetchone()['rank']
            
            conn.execute('''
                INSERT OR REPLACE INTO leaderboard_cache 
                (user_id, username, coins, power, rank, last_update)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, user['username'], user['coins'], user['power'], rank))
    else:
        # Полное обновление лидерборда
        conn.execute('DELETE FROM leaderboard_cache')
        
        users = conn.execute('''
            SELECT user_id, username, coins, power 
            FROM users 
            ORDER BY coins DESC 
            LIMIT 100
        ''').fetchall()
        
        for i, user in enumerate(users, 1):
            conn.execute('''
                INSERT INTO leaderboard_cache 
                (user_id, username, coins, power, rank, last_update)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user['user_id'], user['username'], user['coins'], user['power'], i))
    
    conn.commit()

# Запуск периодического обновления лидерборда
def periodic_leaderboard_update():
    while True:
        time.sleep(60)  # Обновляем каждую минуту
        try:
            conn = get_db()
            update_leaderboard_cache(conn)
            conn.close()
        except:
            pass

# Запускаем в фоне
thread = threading.Thread(target=periodic_leaderboard_update, daemon=True)
thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
