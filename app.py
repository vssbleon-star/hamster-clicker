from flask import Flask, jsonify, request, send_from_directory
import os
import sqlite3
import math
import random
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DB_FILE = os.path.join(BASE_DIR, 'galaxy_clicker.db')

os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'images'), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        username TEXT,
        stardust DECIMAL(30,8) DEFAULT 100.0,
        cosmic_energy DECIMAL(15,2) DEFAULT 100.0,
        energy_capacity DECIMAL(15,2) DEFAULT 100.0,
        energy_regen DECIMAL(10,4) DEFAULT 1.0,
        click_power DECIMAL(20,4) DEFAULT 1.0,
        auto_miners INTEGER DEFAULT 0,
        multiplier DECIMAL(10,4) DEFAULT 1.0,
        total_clicks INTEGER DEFAULT 0,
        galaxy_tier INTEGER DEFAULT 0,
        star_level INTEGER DEFAULT 1,
        experience DECIMAL(15,2) DEFAULT 0,
        dark_matter DECIMAL(15,4) DEFAULT 0,
        artifacts_found INTEGER DEFAULT 0,
        achievements_unlocked INTEGER DEFAULT 0,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS technologies (
        player_id TEXT,
        tech_id TEXT,
        level INTEGER DEFAULT 0,
        researched_at TIMESTAMP,
        PRIMARY KEY (player_id, tech_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS artifacts (
        player_id TEXT,
        artifact_id TEXT,
        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        power_level INTEGER DEFAULT 1,
        PRIMARY KEY (player_id, artifact_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS missions (
        player_id TEXT,
        mission_id TEXT,
        progress DECIMAL(10,2) DEFAULT 0,
        completed BOOLEAN DEFAULT 0,
        completed_at TIMESTAMP,
        PRIMARY KEY (player_id, mission_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cosmic_events (
        player_id TEXT,
        event_id TEXT,
        event_type TEXT,
        multiplier DECIMAL(10,4) DEFAULT 1.0,
        ends_at TIMESTAMP,
        PRIMARY KEY (player_id, event_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboards (
        leaderboard_id TEXT PRIMARY KEY,
        player_id TEXT,
        score DECIMAL(30,8),
        rank INTEGER,
        category TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        player_id TEXT,
        achievement_id TEXT,
        tier INTEGER DEFAULT 0,
        progress DECIMAL(15,2) DEFAULT 0,
        completed BOOLEAN DEFAULT 0,
        completed_at TIMESTAMP,
        PRIMARY KEY (player_id, achievement_id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌟 Cosmic Clicker</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="universe">
        <div class="stars"></div>
        <div class="twinkling"></div>
        <div class="nebula"></div>
    </div>
    
    <div class="container">
        <div class="header">
            <div class="player-info">
                <h1><i class="fas fa-star"></i> COSMIC CLICKER</h1>
                <div class="player-stats">
                    <div class="galaxy-badge">Галактика: <span id="galaxyTier">0</span></div>
                    <div class="star-level">Звезда: <span id="starLevel">1</span></div>
                </div>
            </div>
            <div class="event-indicator" id="eventIndicator"></div>
        </div>

        <div class="resource-panel">
            <div class="resource-card stardust">
                <div class="resource-icon"><i class="fas fa-gem"></i></div>
                <div class="resource-value" id="stardust">100.00</div>
                <div class="resource-label">ЗВЕЗДНАЯ ПЫЛЬ</div>
                <div class="resource-per-second" id="stardustPerSecond">0.00/сек</div>
            </div>
            
            <div class="resource-card energy">
                <div class="resource-icon"><i class="fas fa-bolt"></i></div>
                <div class="resource-value" id="energy">100.0/100.0</div>
                <div class="resource-label">КОСМИЧЕСКАЯ ЭНЕРГИЯ</div>
                <div class="energy-bar">
                    <div class="energy-fill" id="energyFill"></div>
                </div>
            </div>
            
            <div class="resource-card dark-matter">
                <div class="resource-icon"><i class="fas fa-moon"></i></div>
                <div class="resource-value" id="darkMatter">0.0000</div>
                <div class="resource-label">ТЕМНАЯ МАТЕРИЯ</div>
            </div>
        </div>

        <div class="progress-section">
            <div class="star-progress">
                <div class="progress-info">
                    <i class="fas fa-rocket"></i> Прогресс звезды
                    <span class="xp-text">Опыт: <span id="xp">0</span>/<span id="xpNeeded">100</span></span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="xpFill"></div>
                    <div class="progress-milestones"></div>
                </div>
            </div>
            
            <div class="mission-tracker" id="missionTracker">
                <div class="mission-title">Миссия: Начало пути</div>
                <div class="mission-progress">
                    <div class="mission-fill" style="width: 10%"></div>
                </div>
            </div>
        </div>

        <div class="clicker-section">
            <div class="cosmic-center">
                <div class="pulsar-effect"></div>
                <div class="quantum-ring"></div>
                <div class="star-core" id="starCore">
                    <div class="core-inner">
                        <div class="core-glow"></div>
                        <div class="core-particles"></div>
                        <img src="/static/images/star.jpg" alt="Звезда" class="core-image">
                    </div>
                </div>
                <div class="click-stats">
                    <div class="click-power">+<span id="clickPower">1.00</span> звёздной пыли</div>
                    <div class="energy-cost">-<span id="energyCost">1.00</span> энергии</div>
                    <div class="critical-chance">Шанс крита: <span id="critChance">5%</span></div>
                </div>
            </div>
            
            <div class="auto-stats">
                <i class="fas fa-robot"></i> Авто-добыча: 
                <span id="autoIncome">0.00</span>/сек
                <span class="miner-count" id="minerCount">(0 майнеров)</span>
            </div>
        </div>

        <div class="tech-tree">
            <h3><i class="fas fa-atom"></i> ТЕХНОЛОГИИ</h3>
            <div class="tech-branches">
                <div class="tech-branch" data-branch="energy">
                    <div class="branch-icon"><i class="fas fa-bolt"></i></div>
                    <div class="branch-name">Энергетика</div>
                </div>
                <div class="tech-branch" data-branch="mining">
                    <div class="branch-icon"><i class="fas fa-mountain"></i></div>
                    <div class="branch-name">Добыча</div>
                </div>
                <div class="tech-branch" data-branch="multi">
                    <div class="branch-icon"><i class="fas fa-expand-alt"></i></div>
                    <div class="branch-name">Множители</div>
                </div>
                <div class="tech-branch" data-branch="artifacts">
                    <div class="branch-icon"><i class="fas fa-magic"></i></div>
                    <div class="branch-name">Артефакты</div>
                </div>
            </div>
            <div class="tech-nodes" id="techNodes"></div>
        </div>

        <div class="game-tabs">
            <div class="tab-nav">
                <button class="tab-btn active" data-tab="upgrades"><i class="fas fa-arrow-up"></i> Улучшения</button>
                <button class="tab-btn" data-tab="artifacts"><i class="fas fa-magic"></i> Артефакты</button>
                <button class="tab-btn" data-tab="missions"><i class="fas fa-tasks"></i> Миссии</button>
                <button class="tab-btn" data-tab="leaderboard"><i class="fas fa-trophy"></i> Рейтинг</button>
                <button class="tab-btn" data-tab="galaxy"><i class="fas fa-globe"></i> Галактика</button>
            </div>
            
            <div class="tab-content active" id="upgrades">
                <div class="upgrades-grid" id="upgradesGrid"></div>
            </div>
            
            <div class="tab-content" id="artifacts">
                <div class="artifacts-collection" id="artifactsGrid"></div>
            </div>
            
            <div class="tab-content" id="missions">
                <div class="missions-list" id="missionsList"></div>
            </div>
            
            <div class="tab-content" id="leaderboard">
                <div class="leaderboard-filters">
                    <button class="filter-btn active" data-filter="stardust"><i class="fas fa-gem"></i> Богатство</button>
                    <button class="filter-btn" data-filter="power"><i class="fas fa-bolt"></i> Мощность</button>
                    <button class="filter-btn" data-filter="galaxy"><i class="fas fa-globe"></i> Галактики</button>
                    <button class="filter-btn" data-filter="artifacts"><i class="fas fa-magic"></i> Артефакты</button>
                </div>
                <div class="leaderboard-table" id="leaderboardTable"></div>
            </div>
            
            <div class="tab-content" id="galaxy">
                <div class="galaxy-map">
                    <div class="galaxy-info">
                        <h4><i class="fas fa-infinity"></i> СИСТЕМА ГАЛАКТИК</h4>
                        <p>Прокачивайте звезду и переходите в новые галактики!</p>
                    </div>
                    <div class="galaxy-stats">
                        <div>Текущая галактика: <span id="currentGalaxy">Млечный Путь</span></div>
                        <div>Следующая галактика: <span id="nextGalaxy">Андромеда</span></div>
                        <div>Требуется звёздной пыли: <span id="galaxyRequirement">1,000,000</span></div>
                    </div>
                    <button class="galaxy-btn" id="ascendGalaxyBtn"><i class="fas fa-rocket"></i> АСКЕНД В ГАЛАКТИКУ</button>
                </div>
            </div>
        </div>

        <div class="event-banner" id="eventBanner">
            <div class="event-content">
                <i class="fas fa-meteor"></i>
                <span class="event-text">Космический шторм: +50% к добыче!</span>
                <span class="event-timer" id="eventTimer">15:00</span>
            </div>
        </div>
    </div>

    <script src="/static/js/game.js"></script>
    <script>
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(tab).classList.add('active');
                btn.classList.add('active');
                if(tab === 'leaderboard') updateLeaderboard('stardust');
            });
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                updateLeaderboard(btn.dataset.filter);
            });
        });
        
        document.querySelectorAll('.tech-branch').forEach(branch => {
            branch.addEventListener('click', () => {
                const branchId = branch.dataset.branch;
                loadTechNodes(branchId);
            });
        });
    </script>
</body>
</html>
'''

@app.route('/api/player/<player_id>')
def get_player(player_id):
    conn = get_db()
    player = conn.execute('SELECT * FROM players WHERE player_id = ?', (player_id,)).fetchone()
    
    if player:
        data = dict(player)
        
        techs = conn.execute('SELECT tech_id, level FROM technologies WHERE player_id = ?', (player_id,)).fetchall()
        data['technologies'] = {t['tech_id']: t['level'] for t in techs}
        
        artifacts = conn.execute('SELECT artifact_id, power_level FROM artifacts WHERE player_id = ?', (player_id,)).fetchall()
        data['artifacts'] = {a['artifact_id']: a['power_level'] for a in artifacts}
        
        events = conn.execute('SELECT event_type, multiplier, ends_at FROM cosmic_events WHERE player_id = ? AND ends_at > CURRENT_TIMESTAMP', (player_id,)).fetchall()
        data['active_events'] = [dict(e) for e in events]
        
        conn.close()
        return jsonify(data)
    
    conn.close()
    return jsonify({
        'stardust': 100.0,
        'cosmic_energy': 100.0,
        'energy_capacity': 100.0,
        'energy_regen': 1.0,
        'click_power': 1.0,
        'auto_miners': 0,
        'multiplier': 1.0,
        'galaxy_tier': 0,
        'star_level': 1,
        'experience': 0,
        'dark_matter': 0,
        'artifacts_found': 0
    })

@app.route('/api/save', methods=['POST'])
def save_game():
    data = request.json
    player_id = data['player_id']
    username = data.get('username', 'Космический Исследователь')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO players 
        (player_id, username, stardust, cosmic_energy, energy_capacity, energy_regen, 
         click_power, auto_miners, multiplier, total_clicks, galaxy_tier, star_level, 
         experience, dark_matter, artifacts_found, last_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        player_id, username,
        data['stardust'], data['cosmic_energy'], data['energy_capacity'], data['energy_regen'],
        data['click_power'], data['auto_miners'], data['multiplier'], data['total_clicks'],
        data['galaxy_tier'], data['star_level'], data['experience'], data['dark_matter'],
        data.get('artifacts_found', 0)
    ))
    
    conn.commit()
    conn.close()
    
    update_leaderboards(player_id)
    
    return jsonify({'success': True})

@app.route('/api/upgrade', methods=['POST'])
def upgrade_tech():
    data = request.json
    player_id = data['player_id']
    tech_id = data['tech_id']
    cost = data['cost']
    
    conn = get_db()
    cursor = conn.cursor()
    
    player = cursor.execute('SELECT stardust FROM players WHERE player_id = ?', (player_id,)).fetchone()
    
    if player and player['stardust'] >= cost:
        cursor.execute('''
            INSERT OR REPLACE INTO technologies (player_id, tech_id, level, researched_at)
            VALUES (?, ?, COALESCE((SELECT level + 1 FROM technologies WHERE player_id = ? AND tech_id = ?), 1), CURRENT_TIMESTAMP)
        ''', (player_id, tech_id, player_id, tech_id))
        
        cursor.execute('UPDATE players SET stardust = stardust - ? WHERE player_id = ?', (cost, player_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'new_balance': player['stardust'] - cost})
    
    conn.close()
    return jsonify({'success': False, 'error': 'Недостаточно звёздной пыли'})

@app.route('/api/leaderboard/<category>')
def get_leaderboard(category):
    conn = get_db()
    
    if category == 'stardust':
        query = '''
            SELECT player_id, username, stardust, star_level, galaxy_tier, 
                   RANK() OVER (ORDER BY stardust DESC) as rank
            FROM players ORDER BY stardust DESC LIMIT 100
        '''
    elif category == 'power':
        query = '''
            SELECT player_id, username, click_power, star_level, galaxy_tier,
                   RANK() OVER (ORDER BY click_power DESC) as rank
            FROM players ORDER BY click_power DESC LIMIT 100
        '''
    elif category == 'galaxy':
        query = '''
            SELECT player_id, username, galaxy_tier, star_level, stardust,
                   RANK() OVER (ORDER BY galaxy_tier DESC, star_level DESC) as rank
            FROM players ORDER BY galaxy_tier DESC, star_level DESC LIMIT 100
        '''
    else:
        query = '''
            SELECT player_id, username, artifacts_found, star_level, galaxy_tier,
                   RANK() OVER (ORDER BY artifacts_found DESC) as rank
            FROM players ORDER BY artifacts_found DESC LIMIT 100
        '''
    
    players = conn.execute(query).fetchall()
    conn.close()
    
    return jsonify([dict(p) for p in players])

@app.route('/api/missions/<player_id>')
def get_missions(player_id):
    missions = [
        {'id': 'first_click', 'name': 'Первый шаг', 'desc': 'Сделать 10 кликов', 'target': 10, 'reward': 100},
        {'id': 'stardust_100', 'name': 'Богатство', 'desc': 'Накопить 1000 звёздной пыли', 'target': 1000, 'reward': 500},
        {'id': 'energy_500', 'name': 'Энергетик', 'desc': 'Увеличить энергию до 500', 'target': 500, 'reward': 1000},
        {'id': 'miner_5', 'name': 'Автоматизация', 'desc': 'Купить 5 авто-майнеров', 'target': 5, 'reward': 2000},
        {'id': 'artifact_1', 'name': 'Искатель', 'desc': 'Найти первый артефакт', 'target': 1, 'reward': 5000},
    ]
    
    return jsonify(missions)

@app.route('/api/artifacts/discover', methods=['POST'])
def discover_artifact():
    data = request.json
    player_id = data['player_id']
    
    artifacts = [
        {'id': 'crystal_heart', 'name': 'Кристальное Сердце', 'power': 1.5, 'rarity': 'common'},
        {'id': 'quantum_core', 'name': 'Квантовое Ядро', 'power': 2.0, 'rarity': 'rare'},
        {'id': 'stellar_shard', 'name': 'Осколок Звезды', 'power': 3.0, 'rarity': 'epic'},
        {'id': 'black_hole_fragment', 'name': 'Фрагмент Чёрной Дыры', 'power': 5.0, 'rarity': 'legendary'},
    ]
    
    artifact = random.choice(artifacts)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO artifacts (player_id, artifact_id, power_level)
        VALUES (?, ?, ?)
    ''', (player_id, artifact['id'], artifact['power']))
    
    cursor.execute('UPDATE players SET artifacts_found = artifacts_found + 1 WHERE player_id = ?', (player_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'artifact': artifact})

@app.route('/api/ascend', methods=['POST'])
def ascend_galaxy():
    data = request.json
    player_id = data['player_id']
    
    conn = get_db()
    cursor = conn.cursor()
    
    player = cursor.execute('SELECT stardust, galaxy_tier, star_level FROM players WHERE player_id = ?', (player_id,)).fetchone()
    
    requirement = 1000000 * (player['galaxy_tier'] + 1)
    
    if player['stardust'] >= requirement:
        dark_matter = player['stardust'] * 0.001
        cursor.execute('''
            UPDATE players SET 
                galaxy_tier = galaxy_tier + 1,
                stardust = 100,
                cosmic_energy = 100,
                energy_capacity = 100,
                dark_matter = dark_matter + ?,
                last_active = CURRENT_TIMESTAMP
            WHERE player_id = ?
        ''', (dark_matter, player_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'dark_matter_gained': dark_matter})
    
    conn.close()
    return jsonify({'success': False, 'error': 'Недостаточно звёздной пыли'})

@app.route('/api/reset_all')
def reset_all():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM players')
    cursor.execute('DELETE FROM technologies')
    cursor.execute('DELETE FROM artifacts')
    cursor.execute('DELETE FROM missions')
    cursor.execute('DELETE FROM cosmic_events')
    cursor.execute('DELETE FROM leaderboards')
    cursor.execute('DELETE FROM achievements')
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

def update_leaderboards(player_id):
    conn = get_db()
    cursor = conn.cursor()
    
    player = cursor.execute('''
        SELECT stardust, click_power, galaxy_tier, artifacts_found 
        FROM players WHERE player_id = ?
    ''', (player_id,)).fetchone()
    
    if player:
        categories = ['stardust', 'power', 'galaxy', 'artifacts']
        for cat in categories:
            cursor.execute('DELETE FROM leaderboards WHERE player_id = ? AND category = ?', (player_id, cat))
            cursor.execute('''
                INSERT INTO leaderboards (leaderboard_id, player_id, score, category)
                VALUES (?, ?, ?, ?)
            ''', (f'{player_id}_{cat}', player_id, 
                 player['stardust'] if cat == 'stardust' else
                 player['click_power'] if cat == 'power' else
                 player['galaxy_tier'] if cat == 'galaxy' else
                 player['artifacts_found'], cat))
    
    conn.commit()
    conn.close()

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    reset_all()
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Cosmic Clicker запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
