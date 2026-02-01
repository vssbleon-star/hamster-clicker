from flask import Flask, jsonify, request
import os
import time
from datetime import datetime
import sqlite3
import threading

app = Flask(__name__)

# ================= БАЗА ДАННЫХ SQLite =================
DB_FILE = 'hamster.db'

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
    
    conn.commit()
    conn.close()

# Инициализация БД при старте
init_db()

def get_db():
    """Получение соединения с БД"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ================= HTML ИГРА =================
HTML_GAME = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐹 Hamster Empire</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            font-family: Arial, sans-serif;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
            text-align: center;
        }
        
        h1 {
            color: gold;
            margin: 20px 0;
            font-size: 2.5rem;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        
        .stat-value {
            font-size: 24px;
            color: gold;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .hamster {
            width: 150px;
            height: 150px;
            background: gold;
            border-radius: 50%;
            margin: 30px auto;
            cursor: pointer;
            position: relative;
            transition: transform 0.1s;
            box-shadow: 0 10px 20px rgba(255,215,0,0.3);
        }
        
        .hamster:active {
            transform: scale(0.95);
        }
        
        .eye {
            width: 20px;
            height: 20px;
            background: black;
            border-radius: 50%;
            position: absolute;
            top: 40px;
        }
        
        .eye-left { left: 35px; }
        .eye-right { right: 35px; }
        
        .buttons {
            display: grid;
            gap: 10px;
            margin: 20px 0;
        }
        
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
        }
        
        .upgrade { background: #2ecc71; }
        .auto { background: #9b59b6; }
        .leaderboard { background: #e74c3c; }
        
        .tabs {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            margin-top: 20px;
            overflow: hidden;
        }
        
        .tab-header {
            display: flex;
            background: rgba(0,0,0,0.2);
        }
        
        .tab-btn {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
        }
        
        .tab-btn.active {
            background: #3498db;
        }
        
        .tab-content {
            padding: 20px;
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .leaderboard-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .leaderboard-item {
            display: flex;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }
        
        .rank {
            width: 30px;
            height: 30px;
            background: gold;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
            color: #1a1a2e;
        }
        
        .user-info {
            flex: 1;
            text-align: left;
        }
        
        .user-coins {
            color: gold;
            font-weight: bold;
        }
        
        .achievement {
            background: rgba(255,255,255,0.05);
            padding: 10px;
            margin: 5px 0;
            border-radius: 10px;
            text-align: left;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            animation: slideDown 0.3s;
        }
        
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-50px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
        
        @media (max-width: 600px) {
            .stats { grid-template-columns: repeat(2, 1fr); }
            .hamster { width: 120px; height: 120px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐹 Hamster Empire</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="coins">100</div>
                <div class="stat-label">МОНЕТЫ</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="power">1</div>
                <div class="stat-label">СИЛА</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="autos">0</div>
                <div class="stat-label">АВТО</div>
            </div>
        </div>
        
        <div class="hamster" id="hamster">
            <div class="eye eye-left"></div>
            <div class="eye eye-right"></div>
        </div>
        
        <div class="buttons">
            <button class="upgrade" onclick="buyUpgrade()">
                💪 Улучшить (<span id="upgradeCost">50</span> 🪙)
            </button>
            <button class="auto" onclick="buyAuto()">
                🤖 Авто-кликер (<span id="autoCost">100</span> 🪙)
            </button>
            <button class="leaderboard" onclick="showTab('leaderboard')">
                📊 Лидерборд
            </button>
        </div>
        
        <div class="tabs">
            <div class="tab-header">
                <div class="tab-btn active" onclick="showTab('shop')">🛒 Магазин</div>
                <div class="tab-btn" onclick="showTab('leaderboard')">🏆 Топ</div>
                <div class="tab-btn" onclick="showTab('achievements')">⭐ Достижения</div>
            </div>
            
            <div class="tab-content active" id="shop">
                <div style="margin: 10px 0;">
                    <button onclick="buyUpgrade()" style="width: 100%; margin: 5px 0;">
                        💪 +1 сила - 50 🪙
                    </button>
                    <button onclick="buyAuto()" style="width: 100%; margin: 5px 0;">
                        🤖 Авто-кликер - 100 🪙
                    </button>
                    <button onclick="buyMultiplier()" style="width: 100%; margin: 5px 0;">
                        ⚡ x2 множитель - 500 🪙
                    </button>
                </div>
            </div>
            
            <div class="tab-content" id="leaderboard">
                <div class="leaderboard-list" id="leaderboardList">
                    <!-- Лидерборд загрузится здесь -->
                </div>
            </div>
            
            <div class="tab-content" id="achievements">
                <div id="achievementsList">
                    <!-- Достижения загрузятся здесь -->
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Telegram WebApp
        const tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();
        
        let userId = tg.initDataUnsafe.user?.id || 'user_' + Math.random().toString(36).substr(2, 9);
        let username = tg.initDataUnsafe.user?.username || tg.initDataUnsafe.user?.first_name || 'Игрок';
        let coins = 100;
        let power = 1;
        let autos = 0;
        let multiplier = 1;
        let totalClicks = 0;
        let achievements = [];
        
        // Загрузка сохранённой игры
        async function loadGame() {
            try {
                const response = await fetch('/api/user/' + userId);
                if (response.ok) {
                    const data = await response.json();
                    coins = data.coins || 100;
                    power = data.power || 1;
                    autos = data.autos || 0;
                    multiplier = data.multiplier || 1;
                    totalClicks = data.total_clicks || 0;
                }
                updateDisplay();
                updateLeaderboard();
                updateAchievements();
            } catch (error) {
                console.log('Загружаем новую игру');
                updateDisplay();
            }
        }
        
        // Клик по хомяку
        document.getElementById('hamster').onclick = async function(e) {
            const earned = power * multiplier;
            coins += earned;
            totalClicks++;
            
            // Анимация
            this.style.transform = 'scale(0.95)';
            setTimeout(() => this.style.transform = 'scale(1)', 100);
            
            updateDisplay();
            checkAchievements();
            await saveGame();
            
            // Создаем эффект монеты
            const coin = document.createElement('div');
            coin.textContent = `+${earned} 🪙`;
            coin.style.position = 'absolute';
            coin.style.left = e.clientX + 'px';
            coin.style.top = e.clientY + 'px';
            coin.style.color = 'gold';
            coin.style.fontWeight = 'bold';
            coin.style.pointerEvents = 'none';
            coin.style.animation = 'fadeOut 1s';
            
            document.body.appendChild(coin);
            setTimeout(() => coin.remove(), 1000);
        };
        
        // Покупка улучшения
        async function buyUpgrade() {
            const cost = 50 * power;
            if (coins >= cost) {
                coins -= cost;
                power += 1;
                updateDisplay();
                await saveGame();
                showNotification('💪 Сила увеличена до ' + power + '!');
            } else {
                showNotification(`Нужно ${cost} монет!`);
            }
        }
        
        // Покупка авто-кликера
        async function buyAuto() {
            const cost = 100 + (autos * 50);
            if (coins >= cost) {
                coins -= cost;
                autos += 1;
                updateDisplay();
                await saveGame();
                showNotification('🤖 +1 авто-кликер!');
            } else {
                showNotification(`Нужно ${cost} монет!`);
            }
        }
        
        // Покупка множителя
        async function buyMultiplier() {
            const cost = 500;
            if (coins >= cost && multiplier === 1) {
                coins -= cost;
                multiplier = 2;
                updateDisplay();
                await saveGame();
                showNotification('⚡ Множитель x2 активирован!');
            } else if (multiplier > 1) {
                showNotification('Множитель уже активирован!');
            } else {
                showNotification(`Нужно ${cost} монет!`);
            }
        }
        
        // Сохранение игры
        async function saveGame() {
            try {
                await fetch('/api/save', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: userId,
                        username: username,
                        coins: coins,
                        power: power,
                        autos: autos,
                        multiplier: multiplier,
                        total_clicks: totalClicks
                    })
                });
            } catch (error) {
                console.log('Ошибка сохранения:', error);
            }
        }
        
        // Обновление лидерборда
        async function updateLeaderboard() {
            try {
                const response = await fetch('/api/leaderboard');
                const data = await response.json();
                
                const list = document.getElementById('leaderboardList');
                list.innerHTML = '';
                
                data.leaderboard.forEach((user, index) => {
                    const item = document.createElement('div');
                    item.className = 'leaderboard-item';
                    item.innerHTML = `
                        <div class="rank">${index + 1}</div>
                        <div class="user-info">
                            <div>${user.username || 'Игрок'}</div>
                            <div class="user-coins">${user.coins} 🪙</div>
                        </div>
                    `;
                    list.appendChild(item);
                });
            } catch (error) {
                console.log('Ошибка загрузки лидерборда:', error);
            }
        }
        
        // Проверка достижений
        function checkAchievements() {
            const newAchievements = [];
            
            if (totalClicks >= 10 && !achievements.includes('10_clicks')) {
                achievements.push('10_clicks');
                newAchievements.push('10 кликов');
            }
            
            if (totalClicks >= 100 && !achievements.includes('100_clicks')) {
                achievements.push('100_clicks');
                newAchievements.push('100 кликов');
            }
            
            if (coins >= 1000 && !achievements.includes('1000_coins')) {
                achievements.push('1000_coins');
                newAchievements.push('1000 монет');
            }
            
            if (power >= 10 && !achievements.includes('power_10')) {
                achievements.push('power_10');
                newAchievements.push('Сила 10');
            }
            
            if (newAchievements.length > 0) {
                newAchievements.forEach(ach => {
                    showNotification(`🏆 Достижение: ${ach}!`);
                });
                updateAchievements();
            }
        }
        
        // Обновление достижений
        function updateAchievements() {
            const list = document.getElementById('achievementsList');
            list.innerHTML = '';
            
            const allAchievements = [
                {id: '10_clicks', name: 'Новичок', desc: '10 кликов'},
                {id: '100_clicks', name: 'Кликер', desc: '100 кликов'},
                {id: '1000_coins', name: 'Богач', desc: '1000 монет'},
                {id: 'power_10', name: 'Силач', desc: 'Сила 10'}
            ];
            
            allAchievements.forEach(ach => {
                const div = document.createElement('div');
                div.className = 'achievement';
                div.innerHTML = `
                    <div style="font-size: 20px; margin-right: 10px;">
                        ${achievements.includes(ach.id) ? '✅' : '🔒'}
                    </div>
                    <div>
                        <strong>${ach.name}</strong><br>
                        <small>${ach.desc}</small>
                    </div>
                `;
                div.style.display = 'flex';
                div.style.alignItems = 'center';
                list.appendChild(div);
            });
        }
        
        // Обновление отображения
        function updateDisplay() {
            document.getElementById('coins').textContent = coins;
            document.getElementById('power').textContent = power;
            document.getElementById('autos').textContent = autos;
            document.getElementById('upgradeCost').textContent = 50 * power;
            document.getElementById('autoCost').textContent = 100 + (autos * 50);
        }
        
        // Вкладки
        function showTab(tabName) {
            // Скрыть все вкладки
            document.querySelectorAll('.tab-content').forEach(el => {
                el.style.display = 'none';
            });
            
            // Убрать активный класс
            document.querySelectorAll('.tab-btn').forEach(el => {
                el.classList.remove('active');
            });
            
            // Показать нужную вкладку
            document.getElementById(tabName).style.display = 'block';
            
            // Активировать кнопку
            document.querySelectorAll('.tab-btn').forEach(el => {
                if (el.textContent.includes(getTabIcon(tabName))) {
                    el.classList.add('active');
                }
            });
            
            // Обновить данные
            if (tabName === 'leaderboard') updateLeaderboard();
            if (tabName === 'achievements') updateAchievements();
        }
        
        function getTabIcon(tabName) {
            switch(tabName) {
                case 'shop': return '🛒';
                case 'leaderboard': return '🏆';
                case 'achievements': return '⭐';
                default: return '';
            }
        }
        
        // Уведомления
        function showNotification(text) {
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.textContent = text;
            
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 2000);
        }
        
        // Авто-кликеры (каждые 5 секунд)
        setInterval(async () => {
            if (autos > 0) {
                const earned = autos * multiplier;
                coins += earned;
                updateDisplay();
                await saveGame();
                
                if (earned > 0) {
                    showNotification(`🤖 Авто: +${earned} 🪙`);
                }
            }
        }, 5000);
        
        // Запуск игры
        loadGame();
        
        // Добавляем стиль для анимации
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeOut {
                0% { opacity: 1; transform: translateY(0); }
                100% { opacity: 0; transform: translateY(-50px); }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_GAME

# ================= API ЭНДПОИНТЫ =================
@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """Получить данные пользователя"""
    try:
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE user_id = ?', 
            (user_id,)
        ).fetchone()
        conn.close()
        
        if user:
            return jsonify(dict(user))
        return jsonify({
            'coins': 100,
            'power': 1,
            'autos': 0,
            'multiplier': 1,
            'total_clicks': 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # Проверяем существующего пользователя
        user = cursor.execute(
            'SELECT * FROM users WHERE user_id = ?', 
            (user_id,)
        ).fetchone()
        
        if user:
            # Обновляем существующего пользователя
            cursor.execute('''
                UPDATE users SET 
                    username = ?,
                    coins = ?,
                    power = ?,
                    autos = ?,
                    multiplier = ?,
                    total_clicks = ?,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                username,
                data.get('coins', user['coins']),
                data.get('power', user['power']),
                data.get('autos', user['autos']),
                data.get('multiplier', user['multiplier']),
                data.get('total_clicks', user['total_clicks']),
                user_id
            ))
        else:
            # Создаем нового пользователя
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, coins, power, autos, multiplier, total_clicks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
        
        # Обновляем лидерборд
        update_leaderboard_cache(user_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Получить лидерборд"""
    try:
        conn = get_db()
        
        # Если лидерборд пуст, обновляем его
        count = conn.execute('SELECT COUNT(*) as count FROM leaderboard').fetchone()['count']
        if count == 0:
            update_full_leaderboard()
        
        # Получаем лидерборд
        leaderboard = conn.execute('''
            SELECT user_id, username, coins, power, rank
            FROM leaderboard 
            ORDER BY coins DESC 
            LIMIT 20
        ''').fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leaderboard': [dict(row) for row in leaderboard],
            'total_players': count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def update_leaderboard_cache(user_id):
    """Обновить кеш лидерборда для одного пользователя"""
    try:
        conn = get_db()
        
        # Получаем данные пользователя
        user = conn.execute(
            'SELECT * FROM users WHERE user_id = ?', 
            (user_id,)
        ).fetchone()
        
        if user:
            # Считаем ранг
            rank = conn.execute('''
                SELECT COUNT(*) + 1 as rank FROM users 
                WHERE coins > ?
            ''', (user['coins'],)).fetchone()['rank']
            
            # Обновляем или добавляем в лидерборд
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO leaderboard 
                (user_id, username, coins, power, rank)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                user['username'],
                user['coins'],
                user['power'],
                rank
            ))
            
            conn.commit()
        
        conn.close()
    except:
        pass

def update_full_leaderboard():
    """Полное обновление лидерборда"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Очищаем старый лидерборд
        cursor.execute('DELETE FROM leaderboard')
        
        # Получаем топ 100 игроков
        users = conn.execute('''
            SELECT user_id, username, coins, power 
            FROM users 
            ORDER BY coins DESC 
            LIMIT 100
        ''').fetchall()
        
        # Добавляем в лидерборд с рангами
        for i, user in enumerate(users, 1):
            cursor.execute('''
                INSERT INTO leaderboard 
                (user_id, username, coins, power, rank)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user['user_id'],
                user['username'],
                user['coins'],
                user['power'],
                i
            ))
        
        conn.commit()
        conn.close()
    except:
        pass

# Фоновая задача для обновления лидерборда
def background_leaderboard_update():
    """Фоновая задача для периодического обновления лидерборда"""
    while True:
        time.sleep(300)  # Каждые 5 минут
        try:
            update_full_leaderboard()
        except:
            pass

# Запускаем фоновую задачу
thread = threading.Thread(target=background_leaderboard_update, daemon=True)
thread.start()

# Сброс лидерборда (для тестирования)
@app.route('/api/reset', methods=['POST'])
def reset_leaderboard():
    """Сбросить лидерборд (только для теста)"""
    try:
        conn = get_db()
        conn.execute('DELETE FROM leaderboard')
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

# Информация о сервере
@app.route('/api/info', methods=['GET'])
def server_info():
    """Информация о сервере"""
    conn = get_db()
    total_players = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    online_players = conn.execute('''
        SELECT COUNT(*) as count FROM users 
        WHERE last_active > datetime('now', '-5 minutes')
    ''').fetchone()['count']
    conn.close()
    
    return jsonify({
        'status': 'online',
        'total_players': total_players,
        'online_players': online_players,
        'server_time': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
