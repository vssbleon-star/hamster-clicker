from flask import Flask, jsonify, request, send_from_directory
import os
import time
from datetime import datetime
import sqlite3
import threading
import math

app = Flask(__name__)

# ================= НАСТРОЙКА ПУТЕЙ =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DB_FILE = os.path.join(BASE_DIR, 'hamster.db')

# Создаём папки если их нет
os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'images'), exist_ok=True)

# ================= СБРОС ПРОГРЕССА =================
def reset_all_progress():
    """Сброс всего прогресса"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Очищаем все таблицы
    cursor.execute('DELETE FROM users')
    cursor.execute('DELETE FROM leaderboard')
    cursor.execute('DELETE FROM achievements')
    cursor.execute('DELETE FROM upgrades')
    
    conn.commit()
    conn.close()
    print("✅ Весь прогресс сброшен!")

# ================= БАЗА ДАННЫХ =================
def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        coins DECIMAL(20,2) DEFAULT 100,
        energy DECIMAL(10,2) DEFAULT 100,
        max_energy INTEGER DEFAULT 100,
        energy_regen DECIMAL(10,2) DEFAULT 1,
        click_power DECIMAL(10,2) DEFAULT 1,
        autos INTEGER DEFAULT 0,
        multiplier DECIMAL(10,2) DEFAULT 1,
        total_clicks INTEGER DEFAULT 0,
        prestige INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        experience DECIMAL(10,2) DEFAULT 0,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица улучшений
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS upgrades (
        user_id TEXT,
        upgrade_id TEXT,
        level INTEGER DEFAULT 1,
        PRIMARY KEY (user_id, upgrade_id)
    )
    ''')
    
    # Таблица лидерборда
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        coins DECIMAL(20,2),
        click_power DECIMAL(10,2),
        prestige INTEGER,
        level INTEGER,
        rank_coins INTEGER,
        rank_power INTEGER,
        rank_prestige INTEGER,
        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица достижений
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        user_id TEXT,
        achievement_id TEXT,
        progress INTEGER DEFAULT 0,
        unlocked BOOLEAN DEFAULT 0,
        unlocked_at TIMESTAMP,
        PRIMARY KEY (user_id, achievement_id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ================= СТАТИЧЕСКИЕ ФАЙЛЫ =================
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐹 Hamster Empire Pro</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Press+Start+2P&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="stars"></div>
    <div class="twinkling"></div>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1><i class="fas fa-paw"></i> HAMSTER EMPIRE PRO</h1>
                <div class="prestige-badge">Prestige: <span id="prestige">0</span></div>
            </div>
            <div class="online-count">
                <i class="fas fa-users"></i> <span id="onlineCount">0</span>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card gold">
                <div class="stat-icon">💰</div>
                <div class="stat-value" id="coins">100.00</div>
                <div class="stat-label">МОНЕТЫ</div>
            </div>
            <div class="stat-card energy">
                <div class="stat-icon">⚡</div>
                <div class="stat-value" id="energy">100/100</div>
                <div class="stat-label">ЭНЕРГИЯ</div>
                <div class="energy-bar">
                    <div class="energy-fill" id="energyFill"></div>
                </div>
            </div>
            <div class="stat-card power">
                <div class="stat-icon">💪</div>
                <div class="stat-value" id="clickPower">1.00</div>
                <div class="stat-label">СИЛА</div>
            </div>
        </div>

        <div class="level-section">
            <div class="level-info">
                <i class="fas fa-chart-line"></i> Уровень <span id="level">1</span>
                <span class="xp-text">XP: <span id="xp">0</span>/<span id="xpNeeded">100</span></span>
            </div>
            <div class="level-bar">
                <div class="level-fill" id="levelFill"></div>
            </div>
        </div>

        <div class="hamster-section">
            <div class="hamster-container">
                <div class="hamster-glow"></div>
                <div class="hamster" id="hamsterBtn">
                    <div class="hamster-inner">
                        <img src="/static/images/hamster.png" alt="Хомяк" class="hamster-img">
                        <div class="hamster-pulse"></div>
                    </div>
                </div>
                <div class="click-power">+<span id="currentClick">1.00</span> монет</div>
                <div class="energy-cost">-<span id="energyCost">1.00</span> энергии</div>
            </div>
            <div class="auto-income">
                <i class="fas fa-robot"></i> Авто-доход: <span id="autoIncome">0</span>/сек
            </div>
        </div>

        <div class="upgrades-section">
            <h3><i class="fas fa-arrow-up"></i> УЛУЧШЕНИЯ</h3>
            <div class="upgrades-grid" id="upgradesGrid">
                <!-- Улучшения загрузятся через JS -->
            </div>
        </div>

        <div class="tabs">
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="showTab('shop')"><i class="fas fa-shopping-cart"></i> Магазин</button>
                <button class="tab-btn" onclick="showTab('upgrades')"><i class="fas fa-cogs"></i> Прокачка</button>
                <button class="tab-btn" onclick="showTab('leaderboard')"><i class="fas fa-trophy"></i> Лидерборд</button>
                <button class="tab-btn" onclick="showTab('achievements')"><i class="fas fa-medal"></i> Достижения</button>
                <button class="tab-btn" onclick="showTab('prestige')"><i class="fas fa-crown"></i> Престиж</button>
            </div>

            <div class="tab-content active" id="shop">
                <div class="shop-grid" id="shopGrid"></div>
            </div>

            <div class="tab-content" id="upgrades">
                <div class="upgrade-tree" id="upgradeTree"></div>
            </div>

            <div class="tab-content" id="leaderboard">
                <div class="leaderboard-tabs">
                    <button class="lb-tab active" onclick="showLeaderboard('coins')"><i class="fas fa-coins"></i> Богачи</button>
                    <button class="lb-tab" onclick="showLeaderboard('power')"><i class="fas fa-bolt"></i> Силачи</button>
                    <button class="lb-tab" onclick="showLeaderboard('prestige')"><i class="fas fa-crown"></i> Легенды</button>
                    <button class="lb-tab" onclick="showLeaderboard('level')"><i class="fas fa-star"></i> Уровни</button>
                </div>
                <div class="leaderboard-content" id="leaderboardContent"></div>
            </div>

            <div class="tab-content" id="achievements">
                <div class="achievements-grid" id="achievementsGrid"></div>
            </div>

            <div class="tab-content" id="prestige">
                <div class="prestige-content">
                    <h3><i class="fas fa-crown"></i> СИСТЕМА ПРЕСТИЖА</h3>
                    <p>Сбросьте прогресс в обмен на постоянные бонусы!</p>
                    <div class="prestige-stats">
                        <div>Текущий престиж: <span id="currentPrestige">0</span></div>
                        <div>Бонус за престиж: <span id="prestigeBonus">0%</span></div>
                        <div>Требуется монет: <span id="prestigeRequirement">1,000,000</span></div>
                    </div>
                    <button class="prestige-btn" onclick="prestige()"><i class="fas fa-fire"></i> ВОЗНЕСТИСЬ!</button>
                </div>
            </div>
        </div>

        <div class="event-section">
            <div class="event-timer" id="eventTimer"></div>
            <div class="event-reward" id="eventReward"></div>
        </div>
    </div>

    <script src="/static/js/game.js"></script>
    <script>
        let currentTab = 'shop';
        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
            currentTab = tab;
        }
        
        function showLeaderboard(type) {
            // Обновит лидерборд через game.js
        }
    </script>
</body>
</html>
'''

# ================= API =================
@app.route('/api/user/<user_id>')
def get_user(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return jsonify(dict(user))
    else:
        return jsonify({
            'coins': 100,
            'energy': 100,
            'max_energy': 100,
            'energy_regen': 1,
            'click_power': 1,
            'autos': 0,
            'multiplier': 1,
            'prestige': 0,
            'level': 1,
            'experience': 0
        })

@app.route('/api/save', methods=['POST'])
def save_progress():
    data = request.json
    user_id = data['user_id']
    username = data.get('username', 'Игрок')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, coins, energy, max_energy, energy_regen, click_power, 
         autos, multiplier, total_clicks, prestige, level, experience, last_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        user_id, username, 
        data['coins'], data['energy'], data['max_energy'], data['energy_regen'],
        data['click_power'], data['autos'], data['multiplier'], data['total_clicks'],
        data['prestige'], data['level'], data['experience']
    ))
    
    # Обновляем достижения
    update_achievements(user_id, data)
    
    conn.commit()
    conn.close()
    update_leaderboard(user_id)
    
    return jsonify({'success': True})

@app.route('/api/leaderboard/<type>')
def get_leaderboard(type):
    conn = get_db()
    
    if type == 'coins':
        query = 'SELECT user_id, username, coins, level, prestige FROM users ORDER BY coins DESC LIMIT 50'
    elif type == 'power':
        query = 'SELECT user_id, username, click_power, level, prestige FROM users ORDER BY click_power DESC LIMIT 50'
    elif type == 'prestige':
        query = 'SELECT user_id, username, prestige, coins, level FROM users ORDER BY prestige DESC LIMIT 50'
    elif type == 'level':
        query = 'SELECT user_id, username, level, experience, prestige FROM users ORDER BY level DESC LIMIT 50'
    else:
        query = 'SELECT user_id, username, coins, click_power, prestige, level FROM users ORDER BY coins DESC LIMIT 50'
    
    players = conn.execute(query).fetchall()
    conn.close()
    
    return jsonify([dict(p) for p in players])

@app.route('/api/achievements/<user_id>')
def get_achievements(user_id):
    conn = get_db()
    
    # Создаем базовые достижения если их нет
    achievements = [
        ('first_click', 'Первый шаг', 'Сделать первый клик', 1, 'click'),
        ('100_clicks', 'Кликер', '100 кликов', 100, 'click'),
        ('1000_clicks', 'Мастер клика', '1000 кликов', 1000, 'click'),
        ('10000_clicks', 'Король клика', '10000 кликов', 10000, 'click'),
        ('first_coin', 'Первая монета', 'Заработать первую монету', 1, 'coin'),
        ('100_coins', 'Начинающий', '100 монет', 100, 'coin'),
        ('1000_coins', 'Богач', '1000 монет', 1000, 'coin'),
        ('10000_coins', 'Магнат', '10000 монет', 10000, 'coin'),
        ('first_upgrade', 'Улучшатель', 'Купить первое улучшение', 1, 'upgrade'),
        ('10_upgrades', 'Энтузиаст', '10 улучшений', 10, 'upgrade'),
        ('max_energy', 'Энергетик', 'Увеличить энергию до 1000', 1000, 'energy'),
        ('first_prestige', 'Просветленный', 'Первый престиж', 1, 'prestige')
    ]
    
    for ach_id, name, desc, target, type_ in achievements:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO achievements (user_id, achievement_id)
            VALUES (?, ?)
        ''', (user_id, ach_id))
    
    conn.commit()
    
    user_achievements = conn.execute('''
        SELECT a.achievement_id, a.progress, a.unlocked, a.unlocked_at,
               CASE a.achievement_id
        ''' + ''.join([f"WHEN '{ach_id}' THEN '{name}' " for ach_id, name, _, _, _ in achievements]) + '''
               END as name,
               CASE a.achievement_id
        ''' + ''.join([f"WHEN '{ach_id}' THEN '{desc}' " for ach_id, _, desc, _, _ in achievements]) + '''
               END as description,
               CASE a.achievement_id
        ''' + ''.join([f"WHEN '{ach_id}' THEN {target} " for ach_id, _, _, target, _ in achievements]) + '''
               END as target,
               CASE a.achievement_id
        ''' + ''.join([f"WHEN '{ach_id}' THEN '{type_}' " for ach_id, _, _, _, type_ in achievements]) + '''
               END as type
        FROM achievements a WHERE user_id = ?
    ''', (user_id,)).fetchall()
    
    conn.close()
    return jsonify([dict(a) for a in user_achievements])

def update_achievements(user_id, data):
    conn = get_db()
    cursor = conn.cursor()
    
    # Обновляем прогресс достижений
    cursor.execute('''
        UPDATE achievements SET progress = ?
        WHERE user_id = ? AND achievement_id = '100_clicks'
    ''', (data['total_clicks'], user_id))
    
    cursor.execute('''
        UPDATE achievements SET progress = ?
        WHERE user_id = ? AND achievement_id = '100_coins'
    ''', (data['coins'], user_id))
    
    # Разблокируем достижения если выполнены
    cursor.execute('''
        UPDATE achievements SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND progress >= target AND unlocked = 0
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def update_leaderboard(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return
    
    # Обновляем ранги
    cursor.execute('''
        UPDATE leaderboard SET 
            username = ?, coins = ?, click_power = ?, prestige = ?, level = ?,
            rank_coins = (SELECT COUNT(*) + 1 FROM users u2 WHERE u2.coins > ?),
            rank_power = (SELECT COUNT(*) + 1 FROM users u2 WHERE u2.click_power > ?),
            rank_prestige = (SELECT COUNT(*) + 1 FROM users u2 WHERE u2.prestige > ?),
            last_update = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (
        user['username'], user['coins'], user['click_power'], user['prestige'], user['level'],
        user['coins'], user['click_power'], user['prestige'],
        user_id
    ))
    
    if cursor.rowcount == 0:
        cursor.execute('''
            INSERT INTO leaderboard 
            (user_id, username, coins, click_power, prestige, level, rank_coins, rank_power, rank_prestige)
            VALUES (?, ?, ?, ?, ?, ?, 
                (SELECT COUNT(*) + 1 FROM users u2 WHERE u2.coins > ?),
                (SELECT COUNT(*) + 1 FROM users u2 WHERE u2.click_power > ?),
                (SELECT COUNT(*) + 1 FROM users u2 WHERE u2.prestige > ?)
            )
        ''', (
            user_id, user['username'], user['coins'], user['click_power'], 
            user['prestige'], user['level'],
            user['coins'], user['click_power'], user['prestige']
        ))
    
    conn.commit()
    conn.close()

@app.route('/api/reset_all')
def reset_all():
    reset_all_progress()
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    reset_all_progress()
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Hamster Empire Pro запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
