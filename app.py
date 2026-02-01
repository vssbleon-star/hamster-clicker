from flask import Flask, jsonify, request, send_from_directory
import os
import sqlite3
import random
import math
from datetime import datetime, timedelta

app = Flask(__name__)

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DB_FILE = os.path.join(BASE_DIR, 'coin_clicker.db')

os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'images'), exist_ok=True)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Игроки
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        username TEXT,
        coins REAL DEFAULT 0,
        gems INTEGER DEFAULT 10,
        tokens INTEGER DEFAULT 0,
        total_clicks INTEGER DEFAULT 0,
        total_earned REAL DEFAULT 0,
        current_grade INTEGER DEFAULT 0,
        grade_progress REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Улучшения
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS upgrades (
        player_id TEXT,
        upgrade_id TEXT,
        level INTEGER DEFAULT 0,
        purchased_at TIMESTAMP,
        PRIMARY KEY (player_id, upgrade_id)
    )
    ''')
    
    # Автокликеры
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS autoclickers (
        player_id TEXT,
        clicker_id TEXT,
        quantity INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        purchased_at TIMESTAMP,
        PRIMARY KEY (player_id, clicker_id)
    )
    ''')
    
    # Здания
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buildings (
        player_id TEXT,
        building_id TEXT,
        quantity INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        purchased_at TIMESTAMP,
        PRIMARY KEY (player_id, building_id)
    )
    ''')
    
    # Достижения
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        player_id TEXT,
        achievement_id TEXT,
        progress REAL DEFAULT 0,
        completed BOOLEAN DEFAULT 0,
        completed_at TIMESTAMP,
        PRIMARY KEY (player_id, achievement_id)
    )
    ''')
    
    # Ежедневные награды
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_rewards (
        player_id TEXT,
        day INTEGER DEFAULT 1,
        claimed_at TIMESTAMP,
        streak INTEGER DEFAULT 1,
        PRIMARY KEY (player_id, day)
    )
    ''')
    
    # Лидерборд
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        player_id TEXT PRIMARY KEY,
        username TEXT,
        total_score REAL DEFAULT 0,
        coins_score REAL DEFAULT 0,
        grade_score INTEGER DEFAULT 0,
        achievements_score INTEGER DEFAULT 0,
        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Активные бусты
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS active_boosts (
        player_id TEXT,
        boost_id TEXT,
        multiplier REAL DEFAULT 1.0,
        ends_at TIMESTAMP,
        PRIMARY KEY (player_id, boost_id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# HTML страница
HTML_GAME = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💰 Coin Clicker Master</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <!-- Хедер -->
        <header class="main-header">
            <div class="header-top">
                <h1><i class="fas fa-coins"></i> COIN CLICKER MASTER</h1>
                <div class="player-grade">
                    <div class="grade-badge" id="gradeBadge">
                        <span class="grade-icon">🥉</span>
                        <span class="grade-name">BRONZE</span>
                    </div>
                    <div class="grade-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="gradeProgress"></div>
                        </div>
                        <div class="progress-text">Прогресс: <span id="gradePercent">0%</span></div>
                    </div>
                </div>
            </div>
            
            <div class="header-stats">
                <div class="stat-item coins-stat">
                    <div class="stat-icon">💰</div>
                    <div class="stat-content">
                        <div class="stat-value" id="coinsValue">0</div>
                        <div class="stat-label">COINS</div>
                    </div>
                </div>
                
                <div class="stat-item gems-stat">
                    <div class="stat-icon">💎</div>
                    <div class="stat-content">
                        <div class="stat-value" id="gemsValue">10</div>
                        <div class="stat-label">GEMS</div>
                    </div>
                </div>
                
                <div class="stat-item tokens-stat">
                    <div class="stat-icon">🪙</div>
                    <div class="stat-content">
                        <div class="stat-value" id="tokensValue">0</div>
                        <div class="stat-label">TOKENS</div>
                    </div>
                </div>
                
                <div class="stat-item cps-stat">
                    <div class="stat-icon">⚡</div>
                    <div class="stat-content">
                        <div class="stat-value" id="cpsValue">0</div>
                        <div class="stat-label">В СЕКУНДУ</div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Главный кликер -->
        <section class="clicker-section">
            <div class="clicker-container">
                <div class="coin-glow"></div>
                <div class="coin-shine"></div>
                <div class="main-coin" id="mainCoin">
                    <div class="coin-face">
                        <div class="coin-design">
                            <div class="coin-value">$</div>
                            <div class="coin-stars">✦✦✦</div>
                        </div>
                    </div>
                    <div class="coin-sparkles">
                        <div class="sparkle"></div>
                        <div class="sparkle"></div>
                        <div class="sparkle"></div>
                    </div>
                </div>
                <div class="clicker-stats">
                    <div class="click-power">
                        <i class="fas fa-hand-point-up"></i> +<span id="clickPower">1.0</span> за клик
                    </div>
                    <div class="critical-info">
                        <i class="fas fa-fire"></i> Крит: <span id="critChance">5%</span> (x<span id="critMultiplier">2.0</span>)
                    </div>
                    <div class="multi-info">
                        <i class="fas fa-expand-alt"></i> Множитель: x<span id="totalMultiplier">1.0</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- Быстрые улучшения -->
        <section class="quick-upgrades">
            <h3><i class="fas fa-bolt"></i> БЫСТРЫЕ УЛУЧШЕНИЯ</h3>
            <div class="quick-grid">
                <div class="quick-item" onclick="buyUpgrade('click_power')">
                    <div class="quick-icon">💪</div>
                    <div class="quick-name">Усилитель</div>
                    <div class="quick-cost">50 🪙</div>
                </div>
                <div class="quick-item" onclick="buyAutoclicker('basic')">
                    <div class="quick-icon">🤖</div>
                    <div class="quick-name">Автокликер</div>
                    <div class="quick-cost">100 🪙</div>
                </div>
                <div class="quick-item" onclick="buyMultiplier('x2')">
                    <div class="quick-icon">🌀</div>
                    <div class="quick-name">x2 Множитель</div>
                    <div class="quick-cost">500 🪙</div>
                </div>
                <div class="quick-item" onclick="buyCritBoost()">
                    <div class="quick-icon">💥</div>
                    <div class="quick-name">Крит. Удар</div>
                    <div class="quick-cost">200 🪙</div>
                </div>
            </div>
        </section>

        <!-- Панель вкладок -->
        <section class="tabs-section">
            <div class="tabs-header">
                <button class="tab-btn active" data-tab="autoclickers">
                    <i class="fas fa-robot"></i> Автокликеры
                </button>
                <button class="tab-btn" data-tab="upgrades">
                    <i class="fas fa-arrow-up"></i> Улучшения
                </button>
                <button class="tab-btn" data-tab="buildings">
                    <i class="fas fa-city"></i> Здания
                </button>
                <button class="tab-btn" data-tab="achievements">
                    <i class="fas fa-trophy"></i> Достижения
                </button>
                <button class="tab-btn" data-tab="leaderboard">
                    <i class="fas fa-crown"></i> Лидеры
                </button>
            </div>
            
            <div class="tabs-content">
                <!-- Автокликеры -->
                <div class="tab-pane active" id="autoclickers">
                    <div class="clickers-grid" id="clickersGrid"></div>
                </div>
                
                <!-- Улучшения -->
                <div class="tab-pane" id="upgrades">
                    <div class="upgrades-category">
                        <h4><i class="fas fa-hand-rock"></i> Улучшения клика</h4>
                        <div class="upgrades-list" id="clickUpgrades"></div>
                    </div>
                    <div class="upgrades-category">
                        <h4><i class="fas fa-expand-arrows-alt"></i> Множители</h4>
                        <div class="upgrades-list" id="multiplierUpgrades"></div>
                    </div>
                </div>
                
                <!-- Здания -->
                <div class="tab-pane" id="buildings">
                    <div class="buildings-grid" id="buildingsGrid"></div>
                </div>
                
                <!-- Достижения -->
                <div class="tab-pane" id="achievements">
                    <div class="achievements-grid" id="achievementsGrid"></div>
                </div>
                
                <!-- Лидерборд -->
                <div class="tab-pane" id="leaderboard">
                    <div class="leaderboard-filters">
                        <button class="filter-btn active" data-filter="total">
                            <i class="fas fa-trophy"></i> Общий рейтинг
                        </button>
                        <button class="filter-btn" data-filter="coins">
                            <i class="fas fa-coins"></i> Богатство
                        </button>
                        <button class="filter-btn" data-filter="grade">
                            <i class="fas fa-star"></i> Уровень
                        </button>
                        <button class="filter-btn" data-filter="clicks">
                            <i class="fas fa-mouse"></i> Клики
                        </button>
                    </div>
                    <div class="leaderboard-content" id="leaderboardContent"></div>
                </div>
            </div>
        </section>

        <!-- Дневные награды и бусты -->
        <section class="bonus-section">
            <div class="daily-rewards">
                <h4><i class="fas fa-calendar-day"></i> ЕЖЕДНЕВНЫЕ НАГРАДЫ</h4>
                <div class="rewards-track" id="rewardsTrack"></div>
                <button class="claim-btn" id="claimDailyBtn">
                    <i class="fas fa-gift"></i> Получить награду
                </button>
            </div>
            
            <div class="active-boosts">
                <h4><i class="fas fa-bolt"></i> АКТИВНЫЕ БУСТЫ</h4>
                <div class="boosts-list" id="activeBoosts"></div>
            </div>
        </section>

        <!-- Информация о грейдах -->
        <section class="grades-info">
            <h3><i class="fas fa-layer-group"></i> СИСТЕМА ГРЕЙДОВ</h3>
            <div class="grades-track" id="gradesTrack"></div>
            <div class="grade-benefits">
                <h4>Текущие бонусы:</h4>
                <ul id="currentBenefits"></ul>
            </div>
        </section>

        <!-- Футер -->
        <footer class="game-footer">
            <div class="footer-stats">
                <div class="total-clicks">
                    <i class="fas fa-mouse-pointer"></i> Всего кликов: <span id="totalClicks">0</span>
                </div>
                <div class="total-earned">
                    <i class="fas fa-chart-line"></i> Заработано: <span id="totalEarned">0</span>
                </div>
                <div class="play-time">
                    <i class="fas fa-clock"></i> Время игры: <span id="playTime">0</span>
                </div>
            </div>
            <div class="version-info">
                Coin Clicker Master v1.0 | <span id="onlineCount">1</span> игроков онлайн
            </div>
        </footer>
    </div>

    <script src="/static/js/game.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Инициализация вкладок
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const tabId = this.dataset.tab;
                    
                    // Убираем активный класс у всех кнопок и панелей
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                    
                    // Добавляем активный класс
                    this.classList.add('active');
                    document.getElementById(tabId).classList.add('active');
                    
                    // Обновляем контент при переключении
                    if(tabId === 'leaderboard') {
                        game.updateLeaderboard('total');
                    }
                });
            });
            
            // Фильтры лидерборда
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    game.updateLeaderboard(this.dataset.filter);
                });
            });
            
            // Инициализация игры
            game.init();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_GAME

@app.route('/api/player/<player_id>')
def get_player(player_id):
    conn = get_db()
    player = conn.execute('SELECT * FROM players WHERE player_id = ?', (player_id,)).fetchone()
    
    if player:
        data = dict(player)
        
        # Получаем улучшения
        upgrades = conn.execute('SELECT upgrade_id, level FROM upgrades WHERE player_id = ?', (player_id,)).fetchall()
        data['upgrades'] = {u['upgrade_id']: u['level'] for u in upgrades}
        
        # Получаем автокликеры
        autoclickers = conn.execute('SELECT clicker_id, quantity, level FROM autoclickers WHERE player_id = ?', (player_id,)).fetchall()
        data['autoclickers'] = {a['clicker_id']: {'quantity': a['quantity'], 'level': a['level']} for a in autoclickers}
        
        # Получаем здания
        buildings = conn.execute('SELECT building_id, quantity, level FROM buildings WHERE player_id = ?', (player_id,)).fetchall()
        data['buildings'] = {b['building_id']: {'quantity': b['quantity'], 'level': b['level']} for b in buildings}
        
        # Получаем достижения
        achievements = conn.execute('SELECT achievement_id, progress, completed FROM achievements WHERE player_id = ?', (player_id,)).fetchall()
        data['achievements'] = {a['achievement_id']: {'progress': a['progress'], 'completed': a['completed']} for a in achievements}
        
        # Получаем активные бусты
        boosts = conn.execute('SELECT boost_id, multiplier FROM active_boosts WHERE player_id = ? AND ends_at > CURRENT_TIMESTAMP', (player_id,)).fetchall()
        data['active_boosts'] = {b['boost_id']: b['multiplier'] for b in boosts}
        
        conn.close()
        return jsonify(data)
    
    # Создаем нового игрока
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO players (player_id, username, coins, gems, tokens)
        VALUES (?, ?, 0, 10, 0)
    ''', (player_id, 'Игрок'))
    
    # Создаем базовые достижения
    base_achievements = [
        'first_click', 'first_100_coins', 'first_upgrade',
        'first_autoclicker', 'grade_1', 'daily_streak_3'
    ]
    for ach_id in base_achievements:
        cursor.execute('INSERT OR IGNORE INTO achievements (player_id, achievement_id) VALUES (?, ?)', (player_id, ach_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'coins': 0,
        'gems': 10,
        'tokens': 0,
        'total_clicks': 0,
        'total_earned': 0,
        'current_grade': 0,
        'grade_progress': 0,
        'upgrades': {},
        'autoclickers': {},
        'buildings': {},
        'achievements': {},
        'active_boosts': {}
    })

@app.route('/api/save', methods=['POST'])
def save_game():
    data = request.json
    player_id = data['player_id']
    username = data.get('username', 'Игрок')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Обновляем данные игрока
    cursor.execute('''
        UPDATE players SET
            username = ?,
            coins = ?,
            gems = ?,
            tokens = ?,
            total_clicks = ?,
            total_earned = ?,
            current_grade = ?,
            grade_progress = ?,
            last_active = CURRENT_TIMESTAMP
        WHERE player_id = ?
    ''', (
        username,
        data['coins'],
        data['gems'],
        data['tokens'],
        data['total_clicks'],
        data['total_earned'],
        data['current_grade'],
        data['grade_progress'],
        player_id
    ))
    
    # Обновляем лидерборд
    total_score = (
        data['coins'] / 1000 + 
        data['current_grade'] * 1000 + 
        data.get('achievements_completed', 0) * 100
    )
    
    cursor.execute('''
        INSERT OR REPLACE INTO leaderboard 
        (player_id, username, total_score, coins_score, grade_score, achievements_score)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        player_id,
        username,
        total_score,
        data['coins'],
        data['current_grade'],
        data.get('achievements_completed', 0)
    ))
    
    # Обновляем достижения
    for ach_id, ach_data in data.get('achievements', {}).items():
        cursor.execute('''
            UPDATE achievements SET 
                progress = ?,
                completed = ?
            WHERE player_id = ? AND achievement_id = ?
        ''', (ach_data.get('progress', 0), ach_data.get('completed', 0), player_id, ach_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/buy_upgrade', methods=['POST'])
def buy_upgrade():
    data = request.json
    player_id = data['player_id']
    upgrade_id = data['upgrade_id']
    cost = data['cost']
    upgrade_type = data.get('type', 'click')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем баланс
    player = cursor.execute('SELECT coins, gems, tokens FROM players WHERE player_id = ?', (player_id,)).fetchone()
    
    if not player:
        conn.close()
        return jsonify({'success': False, 'error': 'Игрок не найден'})
    
    # Проверяем валюту
    currency_needed = {'coins': player['coins'], 'gems': player['gems'], 'tokens': player['tokens']}
    
    if 'cost_coins' in data and currency_needed['coins'] < data['cost_coins']:
        conn.close()
        return jsonify({'success': False, 'error': 'Недостаточно монет'})
    
    if 'cost_gems' in data and currency_needed['gems'] < data['cost_gems']:
        conn.close()
        return jsonify({'success': False, 'error': 'Недостаточно самоцветов'})
    
    if 'cost_tokens' in data and currency_needed['tokens'] < data['cost_tokens']:
        conn.close()
        return jsonify({'success': False, 'error': 'Недостаточно жетонов'})
    
    # Списание валюты
    if 'cost_coins' in data:
        cursor.execute('UPDATE players SET coins = coins - ? WHERE player_id = ?', (data['cost_coins'], player_id))
    
    if 'cost_gems' in data:
        cursor.execute('UPDATE players SET gems = gems - ? WHERE player_id = ?', (data['cost_gems'], player_id))
    
    if 'cost_tokens' in data:
        cursor.execute('UPDATE players SET tokens = tokens - ? WHERE player_id = ?', (data['cost_tokens'], player_id))
    
    # Добавляем/обновляем улучшение
    if upgrade_type == 'click':
        cursor.execute('''
            INSERT OR REPLACE INTO upgrades (player_id, upgrade_id, level, purchased_at)
            VALUES (?, ?, COALESCE((SELECT level + 1 FROM upgrades WHERE player_id = ? AND upgrade_id = ?), 1), CURRENT_TIMESTAMP)
        ''', (player_id, upgrade_id, player_id, upgrade_id))
    
    elif upgrade_type == 'autoclicker':
        cursor.execute('''
            INSERT OR REPLACE INTO autoclickers (player_id, clicker_id, quantity, purchased_at)
            VALUES (?, ?, COALESCE((SELECT quantity + 1 FROM autoclickers WHERE player_id = ? AND clicker_id = ?), 1), CURRENT_TIMESTAMP)
        ''', (player_id, upgrade_id, player_id, upgrade_id))
    
    elif upgrade_type == 'building':
        cursor.execute('''
            INSERT OR REPLACE INTO buildings (player_id, building_id, quantity, purchased_at)
            VALUES (?, ?, COALESCE((SELECT quantity + 1 FROM buildings WHERE player_id = ? AND building_id = ?), 1), CURRENT_TIMESTAMP)
        ''', (player_id, upgrade_id, player_id, upgrade_id))
    
    conn.commit()
    
    # Получаем обновленные данные
    player = cursor.execute('SELECT coins, gems, tokens FROM players WHERE player_id = ?', (player_id,)).fetchone()
    conn.close()
    
    return jsonify({
        'success': True,
        'new_balance': {
            'coins': player['coins'],
            'gems': player['gems'],
            'tokens': player['tokens']
        }
    })

@app.route('/api/activate_boost', methods=['POST'])
def activate_boost():
    data = request.json
    player_id = data['player_id']
    boost_id = data['boost_id']
    duration = data.get('duration', 300)  # 5 минут по умолчанию
    multiplier = data.get('multiplier', 2.0)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем баланс
    if data.get('cost_gems'):
        player = cursor.execute('SELECT gems FROM players WHERE player_id = ?', (player_id,)).fetchone()
        if player and player['gems'] >= data['cost_gems']:
            cursor.execute('UPDATE players SET gems = gems - ? WHERE player_id = ?', (data['cost_gems'], player_id))
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Недостаточно самоцветов'})
    
    # Добавляем буст
    ends_at = datetime.now() + timedelta(seconds=duration)
    cursor.execute('''
        INSERT OR REPLACE INTO active_boosts (player_id, boost_id, multiplier, ends_at)
        VALUES (?, ?, ?, ?)
    ''', (player_id, boost_id, multiplier, ends_at.isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'ends_at': ends_at.isoformat()})

@app.route('/api/claim_daily', methods=['POST'])
def claim_daily():
    data = request.json
    player_id = data['player_id']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Получаем информацию о ежедневных наградах
    daily = cursor.execute('SELECT * FROM daily_rewards WHERE player_id = ? ORDER BY day DESC LIMIT 1', (player_id,)).fetchone()
    
    now = datetime.now()
    day_reward = 1
    streak = 1
    
    if daily:
        last_claim = datetime.fromisoformat(daily['claimed_at'])
        # Проверяем, прошел ли день
        if (now - last_claim).days >= 1:
            if (now - last_claim).days == 1:
                streak = daily['streak'] + 1
            else:
                streak = 1
            day_reward = daily['day'] + 1 if daily['day'] < 7 else 1
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Уже получали сегодня'})
    else:
        day_reward = 1
    
    # Выдаем награду
    rewards = [
        {'coins': 100, 'gems': 1},
        {'coins': 250, 'gems': 2},
        {'coins': 500, 'gems': 3},
        {'coins': 1000, 'gems': 5},
        {'coins': 2500, 'gems': 8},
        {'coins': 5000, 'gems': 13},
        {'coins': 10000, 'gems': 21, 'tokens': 1}
    ]
    
    reward = rewards[min(day_reward - 1, 6)]
    
    # Умножаем за серию
    if streak > 1:
        reward['coins'] = int(reward['coins'] * (1 + streak * 0.1))
        reward['gems'] = int(reward['gems'] * (1 + streak * 0.1))
    
    # Начисляем награду
    cursor.execute('UPDATE players SET coins = coins + ?, gems = gems + ?, tokens = tokens + ? WHERE player_id = ?',
                  (reward['coins'], reward.get('gems', 0), reward.get('tokens', 0), player_id))
    
    # Записываем факт получения
    cursor.execute('''
        INSERT INTO daily_rewards (player_id, day, claimed_at, streak)
        VALUES (?, ?, ?, ?)
    ''', (player_id, day_reward, now.isoformat(), streak))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'reward': reward,
        'day': day_reward,
        'streak': streak
    })

@app.route('/api/leaderboard/<category>')
def get_leaderboard(category):
    conn = get_db()
    
    if category == 'total':
        query = '''
            SELECT l.*, p.total_clicks 
            FROM leaderboard l
            LEFT JOIN players p ON l.player_id = p.player_id
            ORDER BY l.total_score DESC 
            LIMIT 100
        '''
    elif category == 'coins':
        query = '''
            SELECT l.*, p.total_clicks 
            FROM leaderboard l
            LEFT JOIN players p ON l.player_id = p.player_id
            ORDER BY l.coins_score DESC 
            LIMIT 100
        '''
    elif category == 'grade':
        query = '''
            SELECT l.*, p.total_clicks 
            FROM leaderboard l
            LEFT JOIN players p ON l.player_id = p.player_id
            ORDER BY l.grade_score DESC, l.total_score DESC 
            LIMIT 100
        '''
    elif category == 'clicks':
        query = '''
            SELECT l.*, p.total_clicks 
            FROM leaderboard l
            LEFT JOIN players p ON l.player_id = p.player_id
            ORDER BY p.total_clicks DESC 
            LIMIT 100
        '''
    else:
        query = '''
            SELECT l.*, p.total_clicks 
            FROM leaderboard l
            LEFT JOIN players p ON l.player_id = p.player_id
            ORDER BY l.total_score DESC 
            LIMIT 100
        '''
    
    players = conn.execute(query).fetchall()
    conn.close()
    
    return jsonify([dict(p) for p in players])

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"💰 Coin Clicker Master запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
