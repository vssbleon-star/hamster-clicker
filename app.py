from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Файл для хранения данных
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'users': {}, 'leaderboard': []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def update_leaderboard(data, user_id, username, coins, clicks):
    # Обновляем или добавляем пользователя в лидерборд
    user_exists = False
    for user in data['leaderboard']:
        if user['user_id'] == user_id:
            user['coins'] = coins
            user['clicks'] = clicks
            user['last_active'] = datetime.now().isoformat()
            user_exists = True
            break
    
    if not user_exists:
        data['leaderboard'].append({
            'user_id': user_id,
            'username': username,
            'coins': coins,
            'clicks': clicks,
            'last_active': datetime.now().isoformat()
        })
    
    # Сортируем по монетам (убывание)
    data['leaderboard'] = sorted(data['leaderboard'], 
                                 key=lambda x: x['coins'], 
                                 reverse=True)[:20]  # Топ 20

@app.route('/')
def game():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🐹 Hamster Pro Clicker</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            :root {
                --primary: #667eea;
                --secondary: #764ba2;
                --accent: #f0c040;
            }
            
            body {
                background: linear-gradient(135deg, #1a1a2e, #16213e);
                color: white;
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }
            
            .container {
                max-width: 500px;
                margin: 0 auto;
            }
            
            header {
                text-align: center;
                margin-bottom: 20px;
            }
            
            h1 {
                color: var(--accent);
                font-size: 2.5rem;
                margin: 10px 0;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin: 20px 0;
            }
            
            .stat-card {
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 15px;
                text-align: center;
                backdrop-filter: blur(10px);
            }
            
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: var(--accent);
            }
            
            .stat-label {
                font-size: 12px;
                opacity: 0.8;
            }
            
            .hamster {
                width: 150px;
                height: 150px;
                background: linear-gradient(145deg, var(--accent), #e0a020);
                border-radius: 50%;
                margin: 30px auto;
                cursor: pointer;
                position: relative;
                transition: all 0.1s;
                box-shadow: 0 10px 30px rgba(240, 192, 64, 0.3);
            }
            
            .hamster:active {
                transform: scale(0.95);
                box-shadow: 0 5px 15px rgba(240, 192, 64, 0.5);
            }
            
            .eye {
                width: 20px;
                height: 20px;
                background: black;
                border-radius: 50%;
                position: absolute;
                top: 40px;
            }
            
            .eye.left { left: 35px; }
            .eye.right { right: 35px; }
            
            .buttons {
                display: grid;
                gap: 10px;
                margin: 20px 0;
            }
            
            .btn {
                background: linear-gradient(145deg, var(--primary), var(--secondary));
                color: white;
                border: none;
                padding: 15px;
                border-radius: 12px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .btn:hover {
                transform: translateY(-2px);
            }
            
            .btn.upgrade { background: linear-gradient(145deg, #2ecc71, #27ae60); }
            .btn.auto { background: linear-gradient(145deg, #9b59b6, #8e44ad); }
            .btn.leaderboard { background: linear-gradient(145deg, #e74c3c, #c0392b); }
            
            .tab-container {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                margin-top: 20px;
                overflow: hidden;
            }
            
            .tabs {
                display: flex;
                background: rgba(0,0,0,0.2);
            }
            
            .tab {
                flex: 1;
                padding: 15px;
                text-align: center;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .tab.active {
                background: var(--primary);
            }
            
            .tab-content {
                padding: 20px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .leaderboard-table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .leaderboard-table tr {
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .leaderboard-table td {
                padding: 10px;
            }
            
            .rank {
                color: var(--accent);
                font-weight: bold;
                font-size: 18px;
            }
            
            .username {
                text-align: left;
            }
            
            .coins {
                text-align: right;
                color: var(--accent);
            }
            
            .achievement {
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0;
                display: flex;
                align-items: center;
            }
            
            .achievement-icon {
                font-size: 24px;
                margin-right: 10px;
            }
            
            .particle {
                position: absolute;
                pointer-events: none;
                font-size: 20px;
                animation: float 1s ease-out forwards;
            }
            
            @keyframes float {
                0% { transform: translateY(0) rotate(0deg); opacity: 1; }
                100% { transform: translateY(-100px) rotate(360deg); opacity: 0; }
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
                z-index: 1000;
                animation: slideDown 0.3s ease-out;
            }
            
            @keyframes slideDown {
                from { transform: translateX(-50%) translateY(-50px); opacity: 0; }
                to { transform: translateX(-50%) translateY(0); opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🐹 Hamster Pro</h1>
                <div class="stats-grid">
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
            </header>
            
            <div class="hamster" id="hamster">
                <div class="eye left"></div>
                <div class="eye right"></div>
            </div>
            
            <div class="buttons">
                <button class="btn upgrade" onclick="buyUpgrade()">
                    💪 Улучшить (<span id="upgradeCost">50</span> 🪙)
                </button>
                <button class="btn auto" onclick="buyAuto()">
                    🤖 Авто-кликер (<span id="autoCost">100</span> 🪙)
                </button>
                <button class="btn leaderboard" onclick="showTab('leaderboard')">
                    📊 Топ игроков
                </button>
                <button class="btn" onclick="showTab('achievements')">
                    🏆 Достижения
                </button>
            </div>
            
            <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="showTab('shop')">🛒 Магазин</div>
                    <div class="tab" onclick="showTab('leaderboard')">🏆 Лидерборд</div>
                    <div class="tab" onclick="showTab('achievements')">⭐ Достижения</div>
                </div>
                
                <div class="tab-content" id="shopContent">
                    <h3>Улучшения</h3>
                    <div class="buttons">
                        <button class="btn" onclick="buyUpgrade()">
                            💪 +1 сила (50 🪙)
                        </button>
                        <button class="btn auto" onclick="buyAuto()">
                            🤖 Авто-кликер (100 🪙)
                        </button>
                        <button class="btn" onclick="buyMultiplier()">
                            ⚡ x2 множитель (500 🪙)
                        </button>
                    </div>
                </div>
                
                <div class="tab-content" id="leaderboardContent" style="display: none;">
                    <h3>🏆 Топ игроков</h3>
                    <table class="leaderboard-table" id="leaderboardTable">
                        <tbody id="leaderboardBody">
                            <!-- Лидерборд загрузится здесь -->
                        </tbody>
                    </table>
                </div>
                
                <div class="tab-content" id="achievementsContent" style="display: none;">
                    <h3>⭐ Достижения</h3>
                    <div id="achievementsList">
                        <!-- Достижения загрузятся здесь -->
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Telegram Web App
            const tg = window.Telegram.WebApp;
            tg.expand();
            tg.ready();
            
            let userId = tg.initDataUnsafe.user?.id || 'user_' + Math.random().toString(36).substr(2, 9);
            let username = tg.initDataUnsafe.user?.username || 'Игрок';
            let coins = 100;
            let power = 1;
            let autos = 0;
            let multiplier = 1;
            let totalClicks = 0;
            let achievements = [];
            
            // Загрузка сохранённой игры
            function loadGame() {
                const saved = localStorage.getItem('hamster_save_' + userId);
                if (saved) {
                    const data = JSON.parse(saved);
                    coins = data.coins || 100;
                    power = data.power || 1;
                    autos = data.autos || 0;
                    multiplier = data.multiplier || 1;
                    totalClicks = data.totalClicks || 0;
                    achievements = data.achievements || [];
                }
                updateDisplay();
                updateLeaderboard();
            }
            
            // Клик по хомяку
            document.getElementById('hamster').onclick = async function(e) {
                const earned = power * multiplier;
                coins += earned;
                totalClicks++;
                
                // Анимация
                createParticle(e.clientX, e.clientY, `+${earned} 🪙`);
                this.style.transform = 'scale(0.95)';
                setTimeout(() => this.style.transform = 'scale(1)', 100);
                
                // Вибрация
                if (tg.HapticFeedback) {
                    tg.HapticFeedback.impactOccurred('light');
                }
                
                updateDisplay();
                checkAchievements();
                await saveGame();
                await updateServer();
                
                showNotification(`+${earned} монет! 💰`);
            };
            
            // Покупка улучшения
            function buyUpgrade() {
                const cost = 50 * power;
                if (coins >= cost) {
                    coins -= cost;
                    power += 1;
                    updateDisplay();
                    saveGame();
                    updateServer();
                    showNotification('💪 Сила +1!');
                } else {
                    showNotification(`Нужно ${cost} монет!`);
                }
            }
            
            // Покупка авто-кликера
            function buyAuto() {
                const cost = 100 + (autos * 50);
                if (coins >= cost) {
                    coins -= cost;
                    autos += 1;
                    updateDisplay();
                    saveGame();
                    updateServer();
                    showNotification('🤖 +1 авто-кликер!');
                } else {
                    showNotification(`Нужно ${cost} монет!`);
                }
            }
            
            // Множитель
            function buyMultiplier() {
                const cost = 500;
                if (coins >= cost && multiplier === 1) {
                    coins -= cost;
                    multiplier = 2;
                    updateDisplay();
                    saveGame();
                    updateServer();
                    showNotification('⚡ Множитель x2!');
                } else if (multiplier > 1) {
                    showNotification('Множитель уже куплен!');
                } else {
                    showNotification(`Нужно ${cost} монет!`);
                }
            }
            
            // Сохранение игры
            function saveGame() {
                const data = {
                    coins, power, autos, multiplier, totalClicks, achievements
                };
                localStorage.setItem('hamster_save_' + userId, JSON.stringify(data));
            }
            
            // Обновление на сервере
            async function updateServer() {
                try {
                    const response = await fetch('/api/save', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            user_id: userId,
                            username: username,
                            coins: coins,
                            clicks: totalClicks
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        updateLeaderboard();
                    }
                } catch (error) {
                    console.log('Ошибка сохранения на сервере');
                }
            }
            
            // Обновление лидерборда
            async function updateLeaderboard() {
                try {
                    const response = await fetch('/api/leaderboard');
                    const data = await response.json();
                    
                    const tbody = document.getElementById('leaderboardBody');
                    tbody.innerHTML = '';
                    
                    data.leaderboard.forEach((user, index) => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td class="rank">${index + 1}</td>
                            <td class="username">${user.username || 'Игрок'}</td>
                            <td class="coins">${user.coins} 🪙</td>
                            <td>${user.clicks} 👆</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } catch (error) {
                    console.log('Ошибка загрузки лидерборда');
                }
            }
            
            // Проверка достижений
            function checkAchievements() {
                const newAchievements = [];
                
                if (totalClicks >= 10 && !achievements.includes('10_clicks')) {
                    achievements.push('10_clicks');
                    newAchievements.push({title: 'Новичок', desc: 'Сделать 10 кликов', reward: 50});
                }
                
                if (totalClicks >= 100 && !achievements.includes('100_clicks')) {
                    achievements.push('100_clicks');
                    newAchievements.push({title: 'Кликер', desc: 'Сделать 100 кликов', reward: 100});
                }
                
                if (coins >= 1000 && !achievements.includes('1000_coins')) {
                    achievements.push('1000_coins');
                    newAchievements.push({title: 'Богач', desc: 'Заработать 1000 монет', reward: 200});
                }
                
                if (power >= 10 && !achievements.includes('power_10')) {
                    achievements.push('power_10');
                    newAchievements.push({title: 'Силач', desc: 'Достичь силы 10', reward: 300});
                }
                
                if (newAchievements.length > 0) {
                    coins += newAchievements.reduce((sum, ach) => sum + ach.reward, 0);
                    updateDisplay();
                    saveGame();
                    
                    newAchievements.forEach(ach => {
                        showNotification(`🏆 ${ach.title}: +${ach.reward} монет!`);
                    });
                }
                
                updateAchievementsDisplay();
            }
            
            // Отображение достижений
            function updateAchievementsDisplay() {
                const list = document.getElementById('achievementsList');
                list.innerHTML = '';
                
                const allAchievements = [
                    {id: '10_clicks', title: 'Новичок', desc: '10 кликов', reward: 50},
                    {id: '100_clicks', title: 'Кликер', desc: '100 кликов', reward: 100},
                    {id: '1000_coins', title: 'Богач', desc: '1000 монет', reward: 200},
                    {id: 'power_10', title: 'Силач', desc: 'Сила 10', reward: 300},
                ];
                
                allAchievements.forEach(ach => {
                    const div = document.createElement('div');
                    div.className = 'achievement';
                    div.innerHTML = `
                        <div class="achievement-icon">
                            ${achievements.includes(ach.id) ? '✅' : '🔒'}
                        </div>
                        <div>
                            <strong>${ach.title}</strong><br>
                            <small>${ach.desc}</small><br>
                            <small>Награда: ${ach.reward} 🪙</small>
                        </div>
                    `;
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
                
                // Убрать активный класс у всех вкладок
                document.querySelectorAll('.tab').forEach(el => {
                    el.classList.remove('active');
                });
                
                // Показать нужную вкладку
                document.getElementById(tabName + 'Content').style.display = 'block';
                
                // Активировать нужную кнопку
                document.querySelectorAll('.tab').forEach(el => {
                    if (el.textContent.includes(getTabIcon(tabName))) {
                        el.classList.add('active');
                    }
                });
                
                // Обновить данные если нужно
                if (tabName === 'leaderboard') updateLeaderboard();
                if (tabName === 'achievements') updateAchievementsDisplay();
            }
            
            function getTabIcon(tabName) {
                switch(tabName) {
                    case 'shop': return '🛒';
                    case 'leaderboard': return '🏆';
                    case 'achievements': return '⭐';
                    default: return '';
                }
            }
            
            // Частицы
            function createParticle(x, y, text) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.textContent = text;
                particle.style.left = (x - 30) + 'px';
                particle.style.top = (y - 30) + 'px';
                particle.style.color = '#f0c040';
                
                document.body.appendChild(particle);
                setTimeout(() => particle.remove(), 1000);
            }
            
            // Уведомления
            function showNotification(text) {
                const notification = document.createElement('div');
                notification.className = 'notification';
                notification.textContent = text;
                
                document.body.appendChild(notification);
                setTimeout(() => notification.remove(), 2000);
            }
            
            // Авто-кликеры
            setInterval(() => {
                if (autos > 0) {
                    const earned = autos * multiplier;
                    coins += earned;
                    updateDisplay();
                    saveGame();
                    updateServer();
                    
                    if (earned > 0) {
                        showNotification(`🤖 Авто: +${earned} 🪙`);
                    }
                }
            }, 30000); // Каждые 30 секунд
            
            // Запуск
            loadGame();
            updateLeaderboard();
            updateAchievementsDisplay();
            
            // Периодическое обновление лидерборда
            setInterval(updateLeaderboard, 30000);
        </script>
    </body>
    </html>
    '''

# API для сохранения данных
@app.route('/api/save', methods=['POST'])
def api_save():
    try:
        data = request.json
        user_id = str(data['user_id'])
        username = data.get('username', 'Игрок')
        coins = data.get('coins', 0)
        clicks = data.get('clicks', 0)
        
        db = load_data()
        
        # Сохраняем данные пользователя
        if 'users' not in db:
            db['users'] = {}
        
        db['users'][user_id] = {
            'username': username,
            'coins': coins,
            'clicks': clicks,
            'last_update': datetime.now().isoformat()
        }
        
        # Обновляем лидерборд
        update_leaderboard(db, user_id, username, coins, clicks)
        
        save_data(db)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API для получения лидерборда
@app.route('/api/leaderboard')
def api_leaderboard():
    db = load_data()
    return jsonify(db)

# Корректный запуск для Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
