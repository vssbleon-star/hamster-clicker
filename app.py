from flask import Flask, jsonify, request, send_from_directory
import os
import time
from datetime import datetime
import sqlite3
import threading

app = Flask(__name__)

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
        /* Дополнительные стили */
        .particle {
            position: absolute;
            pointer-events: none;
            font-size: 20px;
            z-index: 1000;
            animation: floatUp 1s ease-out forwards;
        }
        
        @keyframes floatUp {
            0% { opacity: 1; transform: translateY(0) scale(1); }
            100% { opacity: 0; transform: translateY(-100px) scale(1.5); }
        }
        
        .level-bar {
            width: 100%;
            height: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
            margin: 10px 0;
            overflow: hidden;
        }
        
        .level-fill {
            height: 100%;
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
            border-radius: 5px;
            transition: width 0.5s;
        }
        
        .achievement-badge {
            display: inline-block;
            background: rgba(255,215,0,0.2);
            border: 2px solid gold;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            line-height: 36px;
            text-align: center;
            margin: 5px;
            font-size: 20px;
        }
        
        .shop-item {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid transparent;
            transition: all 0.3s;
        }
        
        .shop-item:hover {
            border-color: #6366f1;
            transform: translateY(-5px);
        }
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
        
        <!-- Уровень -->
        <div style="margin: 20px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span><i class="fas fa-chart-line"></i> Уровень <span id="level">1</span></span>
                <span id="xp">0/100</span>
            </div>
            <div class="level-bar">
                <div class="level-fill" id="levelFill" style="width: 0%"></div>
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
            <button class="btn" onclick="buyMultiplier()" style="background: linear-gradient(145deg, #f59e0b, #d97706);">
                <i class="fas fa-rocket"></i> Буст x2
                <div class="btn-cost"><span id="multiplierCost">500</span> <i class="fas fa-coins"></i></div>
            </button>
            <button class="btn" onclick="showTab('leaderboard')" style="background: linear-gradient(145deg, #ef4444, #dc2626);">
                <i class="fas fa-trophy"></i> Лидерборд
            </button>
        </div>
        
        <!-- Вкладки -->
        <div class="tabs">
            <div class="tab-header">
                <div class="tab-btn active" onclick="showTab('shop')"><i class="fas fa-shopping-cart"></i> Магазин</div>
                <div class="tab-btn" onclick="showTab('leaderboard')"><i class="fas fa-trophy"></i> Топ</div>
                <div class="tab-btn" onclick="showTab('achievements')"><i class="fas fa-star"></i> Достижения</div>
                <div class="tab-btn" onclick="showTab('stats')"><i class="fas fa-chart-bar"></i> Статистика</div>
            </div>
            
            <div class="tab-content active" id="shop">
                <h3><i class="fas fa-store"></i> Магазин улучшений</h3>
                <div id="shopItems">
                    <!-- Товары загрузятся через JS -->
                </div>
            </div>
            
            <div class="tab-content" id="leaderboard">
                <h3><i class="fas fa-crown"></i> Топ игроков</h3>
                <div class="leaderboard-list" id="leaderboardList">
                    <!-- Лидерборд загрузится здесь -->
                </div>
                <button onclick="updateLeaderboard()" style="margin-top: 15px; width: 100%;">
                    <i class="fas fa-sync-alt"></i> Обновить
                </button>
            </div>
            
            <div class="tab-content" id="achievements">
                <h3><i class="fas fa-medal"></i> Достижения</h3>
                <div id="achievementsList">
                    <!-- Достижения загрузятся здесь -->
                </div>
            </div>
            
            <div class="tab-content" id="stats">
                <h3><i class="fas fa-user-chart"></i> Ваша статистика</h3>
                <div id="statsContent">
                    <!-- Статистика загрузится здесь -->
                </div>
            </div>
        </div>
        
        <!-- Прогресс дня -->
        <div style="margin-top: 25px; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <i class="fas fa-calendar-day"></i> Ежедневная цель
                </div>
                <div id="dailyProgress">0/10 кликов</div>
            </div>
            <div class="level-bar" style="height: 8px; margin: 10px 0;">
                <div class="level-fill" id="dailyFill" style="width: 0%"></div>
            </div>
            <button onclick="claimDaily()" id="dailyButton" style="width: 100%;" disabled>
                <i class="fas fa-gift"></i> Получить награду (0/10)
            </button>
        </div>
    </div>
    
    <!-- Подключение JavaScript -->
    <script src="/static/js/game.js"></script>
    <script>
        // Основной код игры
        const game = {
            coins: 100,
            power: 1,
            autos: 0,
            multiplier: 1,
            totalClicks: 0,
            level: 1,
            xp: 0,
            dailyClicks: 0,
            userId: null,
            username: 'Игрок',
            
            init() {
                // Telegram WebApp
                if (window.Telegram && window.Telegram.WebApp) {
                    const tg = window.Telegram.WebApp;
                    tg.expand();
                    tg.ready();
                    
                    this.userId = tg.initDataUnsafe.user?.id || 'user_' + Math.random().toString(36).substr(2, 9);
                    this.username = tg.initDataUnsafe.user?.username || tg.initDataUnsafe.user?.first_name || 'Игрок';
                    
                    // Меняем тему под Telegram
                    if (tg.colorScheme === 'dark') {
                        document.body.style.background = '#0f172a';
                    }
                }
                
                this.loadGame();
                this.setupEventListeners();
                this.startAutoClickers();
                this.updateShop();
                this.updateStats();
                
                // Проверяем изображение хомяка
                const hamsterImg = document.getElementById('hamsterImage');
                hamsterImg.onload = () => {
                    document.getElementById('hamsterFace').style.display = 'none';
                    hamsterImg.style.display = 'block';
                };
                hamsterImg.onerror = () => {
                    hamsterImg.style.display = 'none';
                    document.getElementById('hamsterFace').style.display = 'block';
                };
            },
            
            loadGame() {
                // Загрузка из localStorage
                const saved = localStorage.getItem('hamster_save_' + this.userId);
                if (saved) {
                    const data = JSON.parse(saved);
                    this.coins = data.coins || 100;
                    this.power = data.power || 1;
                    this.autos = data.autos || 0;
                    this.multiplier = data.multiplier || 1;
                    this.totalClicks = data.totalClicks || 0;
                    this.level = data.level || 1;
                    this.xp = data.xp || 0;
                    this.dailyClicks = data.dailyClicks || 0;
                }
                
                this.updateDisplay();
                this.updateLeaderboard();
                this.updateAchievements();
                this.checkDailyReset();
            },
            
            saveGame() {
                const data = {
                    coins: this.coins,
                    power: this.power,
                    autos: this.autos,
                    multiplier: this.multiplier,
                    totalClicks: this.totalClicks,
                    level: this.level,
                    xp: this.xp,
                    dailyClicks: this.dailyClicks,
                    lastSave: Date.now()
                };
                
                localStorage.setItem('hamster_save_' + this.userId, JSON.stringify(data));
                
                // Сохраняем на сервер
                this.saveToServer();
            },
            
            async saveToServer() {
                try {
                    const response = await fetch('/api/save', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            user_id: this.userId,
                            username: this.username,
                            coins: this.coins,
                            power: this.power,
                            autos: this.autos,
                            multiplier: this.multiplier,
                            total_clicks: this.totalClicks
                        })
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        if (data.success) {
                            this.updateLeaderboard();
                        }
                    }
                } catch (error) {
                    console.log('Ошибка сохранения:', error);
                }
            },
            
            clickHamster(event) {
                const earned = this.power * this.multiplier;
                this.coins += earned;
                this.totalClicks++;
                this.dailyClicks++;
                this.addXP(1);
                
                // Анимация
                const hamster = document.getElementById('hamsterBtn');
                hamster.style.transform = 'scale(0.95)';
                setTimeout(() => hamster.style.transform = 'scale(1)', 100);
                
                // Эффект монеты
                this.createParticle(event.clientX, event.clientY, `+${earned} 🪙`, '#f59e0b');
                
                this.updateDisplay();
                this.checkAchievements();
                this.saveGame();
                
                // Вибрация если доступна
                if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
                    window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
                }
                
                return earned;
            },
            
            buyUpgrade() {
                const cost = 50 * this.power;
                if (this.coins >= cost) {
                    this.coins -= cost;
                    this.power += 1;
                    this.updateDisplay();
                    this.saveGame();
                    this.showNotification(`💪 Сила увеличена до ${this.power}!`);
                    return true;
                }
                this.showNotification(`❌ Нужно ${cost} монет!`);
                return false;
            },
            
            buyAuto() {
                const cost = 100 + (this.autos * 50);
                if (this.coins >= cost) {
                    this.coins -= cost;
                    this.autos += 1;
                    this.updateDisplay();
                    this.saveGame();
                    this.showNotification(`🤖 Куплен авто-кликер #${this.autos}!`);
                    return true;
                }
                this.showNotification(`❌ Нужно ${cost} монет!`);
                return false;
            },
            
            buyMultiplier() {
                const cost = 500;
                if (this.coins >= cost && this.multiplier === 1) {
                    this.coins -= cost;
                    this.multiplier = 2;
                    this.updateDisplay();
                    this.saveGame();
                    this.showNotification(`⚡ Активирован множитель x2!`);
                    
                    // Множитель на 5 минут
                    setTimeout(() => {
                        if (this.multiplier === 2) {
                            this.multiplier = 1;
                            this.updateDisplay();
                            this.showNotification('Множитель x2 закончился');
                        }
                    }, 300000); // 5 минут
                    
                    return true;
                } else if (this.multiplier > 1) {
                    this.showNotification('🎯 Множитель уже активен!');
                } else {
                    this.showNotification(`❌ Нужно ${cost} монет!`);
                }
                return false;
            },
            
            addXP(amount) {
                this.xp += amount;
                const xpForNextLevel = this.level * 100;
                
                if (this.xp >= xpForNextLevel) {
                    this.xp -= xpForNextLevel;
                    this.level += 1;
                    this.coins += this.level * 50;
                    this.showNotification(`🎉 Уровень ${this.level}! +${this.level * 50} монет`);
                }
                
                this.updateDisplay();
            },
            
            updateDisplay() {
                // Обновляем статистику
                document.getElementById('coins').textContent = this.coins;
                document.getElementById('power').textContent = this.power;
                document.getElementById('autos').textContent = this.autos;
                document.getElementById('multiplier').textContent = this.multiplier + 'x';
                document.getElementById('upgradeCost').textContent = 50 * this.power;
                document.getElementById('autoCost').textContent = 100 + (this.autos * 50);
                document.getElementById('multiplierCost').textContent = 500;
                
                // Уровень и XP
                document.getElementById('level').textContent = this.level;
                const xpForNextLevel = this.level * 100;
                document.getElementById('xp').textContent = `${this.xp}/${xpForNextLevel}`;
                const xpPercent = (this.xp / xpForNextLevel) * 100;
                document.getElementById('levelFill').style.width = xpPercent + '%';
                
                // Ежедневная цель
                document.getElementById('dailyProgress').textContent = `${this.dailyClicks}/10 кликов`;
                const dailyPercent = Math.min((this.dailyClicks / 10) * 100, 100);
                document.getElementById('dailyFill').style.width = dailyPercent + '%';
                
                const dailyButton = document.getElementById('dailyButton');
                if (this.dailyClicks >= 10) {
                    dailyButton.disabled = false;
                    dailyButton.innerHTML = '<i class="fas fa-gift"></i> Получить награду!';
                    dailyButton.style.background = 'linear-gradient(145deg, #f59e0b, #d97706)';
                } else {
                    dailyButton.disabled = true;
                    dailyButton.innerHTML = `<i class="fas fa-gift"></i> Получить награду (${this.dailyClicks}/10)`;
                    dailyButton.style.background = '';
                }
            },
            
            createParticle(x, y, text, color = '#f59e0b') {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.textContent = text;
                particle.style.left = (x - 20) + 'px';
                particle.style.top = (y - 20) + 'px';
                particle.style.color = color;
                particle.style.fontWeight = 'bold';
                particle.style.fontSize = '18px';
                
                document.body.appendChild(particle);
                setTimeout(() => particle.remove(), 1000);
            },
            
            showNotification(text) {
                const notification = document.createElement('div');
                notification.className = 'notification';
                notification.textContent = text;
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0,0,0,0.9);
                    color: white;
                    padding: 12px 24px;
                    border-radius: 12px;
                    z-index: 1000;
                    animation: slideDown 0.3s ease-out;
                    border-left: 4px solid #f59e0b;
                    max-width: 90%;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.3);
                `;
                
                document.body.appendChild(notification);
                setTimeout(() => notification.remove(), 2000);
            },
            
            setupEventListeners() {
                // Клик по хомяку
                const hamster = document.getElementById('hamsterBtn');
                if (hamster) {
                    hamster.addEventListener('click', (e) => {
                        this.clickHamster(e);
                    });
                }
                
                // Кнопки
                document.querySelector('.btn.upgrade')?.addEventListener('click', () => this.buyUpgrade());
                document.querySelector('.btn.auto')?.addEventListener('click', () => this.buyAuto());
                document.querySelector('.btn[onclick*="buyMultiplier"]')?.addEventListener('click', () => this.buyMultiplier());
                document.querySelector('#dailyButton')?.addEventListener('click', () => this.claimDaily());
            },
            
            startAutoClickers() {
                // Авто-кликеры каждые 3 секунды
                setInterval(() => {
                    if (this.autos > 0) {
                        const earned = this.autos * this.multiplier;
                        if (earned > 0) {
                            this.coins += earned;
                            this.updateDisplay();
                            this.saveGame();
                            
                            // Случайный эффект авто-кликера
                            if (Math.random() > 0.7) {
                                const x = 50 + Math.random() * 50;
                                const y = 50 + Math.random() * 50;
                                this.createParticle(
                                    window.innerWidth * (x / 100),
                                    window.innerHeight * (y / 100),
                                    `🤖 +${earned}`,
                                    '#9b59b6'
                                );
                            }
                        }
                    }
                }, 3000);
            },
            
            updateShop() {
                const shopItems = document.getElementById('shopItems');
                if (!shopItems) return;
                
                const items = [
                    {id: 'upgrade', name: 'Улучшение силы', desc: '+1 к силе клика', cost: () => 50 * this.power, icon: '⚡'},
                    {id: 'auto', name: 'Авто-кликер', desc: 'Автоматически кликает', cost: () => 100 + (this.autos * 50), icon: '🤖'},
                    {id: 'multiplier', name: 'Буст x2', desc: 'Удваивает доход на 5 мин', cost: () => 500, icon: '🚀'},
                    {id: 'power_boost', name: 'Мега-усиление', desc: '+5 силы сразу', cost: () => 1000, icon: '💎'},
                ];
                
                shopItems.innerHTML = items.map(item => `
                    <div class="shop-item" onclick="game.buyItem('${item.id}')">
                        <div style="font-size: 24px; margin-bottom: 10px;">${item.icon}</div>
                        <div style="font-weight: bold; margin-bottom: 5px;">${item.name}</div>
                        <div style="font-size: 14px; opacity: 0.8; margin-bottom: 10px;">${item.desc}</div>
                        <div style="color: #f59e0b; font-weight: bold;">
                            ${item.cost()} <i class="fas fa-coins"></i>
                        </div>
                    </div>
                `).join('');
            },
            
            buyItem(itemId) {
                switch(itemId) {
                    case 'upgrade': this.buyUpgrade(); break;
                    case 'auto': this.buyAuto(); break;
                    case 'multiplier': this.buyMultiplier(); break;
                    case 'power_boost': this.buyPowerBoost(); break;
                }
                this.updateShop();
            },
            
            buyPowerBoost() {
                const cost = 1000;
                if (this.coins >= cost) {
                    this.coins -= cost;
                    this.power += 5;
                    this.updateDisplay();
                    this.saveGame();
                    this.showNotification('💎 +5 силы!');
                    return true;
                }
                this.showNotification(`❌ Нужно ${cost} монет!`);
                return false;
            },
            
            async updateLeaderboard() {
                try {
                    const response = await fetch('/api/leaderboard');
                    if (response.ok) {
                        const data = await response.json();
                        const list = document.getElementById('leaderboardList');
                        
                        if (list && data.leaderboard) {
                            list.innerHTML = data.leaderboard.map((user, index) => `
                                <div class="leaderboard-item">
                                    <div class="rank ${index < 3 ? 'rank-' + (index + 1) : ''}">
                                        ${index + 1}
                                    </div>
                                    <div class="user-info">
                                        <div class="user-name">${user.username || 'Игрок'}</div>
                                        <div class="user-stats">
                                            <span><i class="fas fa-coins"></i> ${user.coins}</span>
                                            <span><i class="fas fa-bolt"></i> ${user.power}</span>
                                        </div>
                                    </div>
                                </div>
                            `).join('');
                        }
                    }
                } catch (error) {
                    console.log('Ошибка загрузки лидерборда:', error);
                }
            },
            
            updateAchievements() {
                const list = document.getElementById('achievementsList');
                if (!list) return;
                
                const achievements = [
                    {id: 'first_click', name: 'Первый шаг', desc: 'Сделать первый клик', icon: '🎯'},
                    {id: '100_clicks', name: 'Кликер', desc: '100 кликов', icon: '👆'},
                    {id: '1000_coins', name: 'Богач', desc: '1000 монет', icon: '💰'},
                    {id: 'power_10', name: 'Силач', desc: 'Сила 10', icon: '💪'},
                    {id: 'auto_5', name: 'Автоматизатор', desc: '5 авто-кликеров', icon: '🤖'},
                ];
                
                // Проверяем выполненные достижения
                const completed = [];
                if (this.totalClicks >= 1) completed.push('first_click');
                if (this.totalClicks >= 100) completed.push('100_clicks');
                if (this.coins >= 1000) completed.push('1000_coins');
                if (this.power >= 10) completed.push('power_10');
                if (this.autos >= 5) completed.push('auto_5');
                
                list.innerHTML = achievements.map(ach => `
                    <div class="achievement" style="opacity: ${completed.includes(ach.id) ? '1' : '0.5'};">
                        <div style="font-size: 24px; margin-right: 15px;">${ach.icon}</div>
                        <div>
                            <div style="font-weight: bold;">${ach.name}</div>
                            <div style="font-size: 14px; opacity: 0.8;">${ach.desc}</div>
                            <div style="font-size: 12px; margin-top: 5px;">
                                ${completed.includes(ach.id) ? '✅ Выполнено' : '❌ Не выполнено'}
                            </div>
                        </div>
                    </div>
                `).join('');
            },
            
            checkAchievements() {
                // Проверяем и разблокируем достижения
                const newAchievements = [];
                
                if (this.totalClicks === 1) newAchievements.push('🎯 Первый клик!');
                if (this.totalClicks === 100) newAchievements.push('👆 100 кликов!');
                if (this.coins >= 1000) newAchievements.push('💰 1000 монет!');
                if (this.power >= 10) newAchievements.push('💪 Сила 10!');
                if (this.autos >= 5) newAchievements.push('🤖 5 авто-кликеров!');
                
                if (newAchievements.length > 0) {
                    newAchievements.forEach(ach => {
                        this.showNotification(`🏆 Достижение: ${ach}`);
                    });
                    this.updateAchievements();
                }
            },
            
            updateStats() {
                const statsContent = document.getElementById('statsContent');
                if (!statsContent) return;
                
                statsContent.innerHTML = `
                    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Всего кликов:</span>
                            <span style="color: #f59e0b; font-weight: bold;">${this.totalClicks}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Заработано монет:</span>
                            <span style="color: #f59e0b; font-weight: bold;">${this.coins}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Доход в секунду:</span>
                            <span style="color: #2ecc71; font-weight: bold;">${this.autos * this.multiplier}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Игровой ID:</span>
                            <span style="font-family: monospace; font-size: 12px;">${this.userId.substring(0, 8)}...</span>
                        </div>
                    </div>
                `;
            },
            
            claimDaily() {
                if (this.dailyClicks >= 10) {
                    const reward = 100 + (this.level * 20);
                    this.coins += reward;
                    this.dailyClicks = 0;
                    this.updateDisplay();
                    this.saveGame();
                    this.showNotification(`🎁 Ежедневная награда: +${reward} монет!`);
                }
            },
            
            checkDailyReset() {
                // Сброс ежедневного прогресса если прошло больше 24 часа
                const lastSave = localStorage.getItem('hamster_last_daily_reset');
                const now = Date.now();
                
                if (!lastSave || (now - parseInt(lastSave)) > 24 * 60 * 60 * 1000) {
                    this.dailyClicks = 0;
                    localStorage.setItem('hamster_last_daily_reset', now.toString());
                }
            }
        };
        
        // Глобальный объект игры
        window.game = game;
        
        // Вспомогательные функции
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
            const tab = document.getElementById(tabName);
            if (tab) {
                tab.style.display = 'block';
            }
            
            // Активировать кнопку
            document.querySelectorAll('.tab-btn').forEach(btn => {
                if (btn.textContent.includes(getTabIcon(tabName))) {
                    btn.classList.add('active');
                }
            });
            
            // Обновить данные
            if (tabName === 'leaderboard') game.updateLeaderboard();
            if (tabName === 'achievements') game.updateAchievements();
            if (tabName === 'stats') game.updateStats();
            if (tabName === 'shop') game.updateShop();
        }
        
        function getTabIcon(tabName) {
            const icons = {
                'shop': '🛒',
                'leaderboard': '🏆',
                'achievements': '⭐',
                'stats': '📊'
            };
            return icons[tabName] || '';
        }
        
        function updateLeaderboard() {
            game.updateLeaderboard();
            game.showNotification('🔄 Лидерборд обновлён!');
        }
        
        // Запуск игры
        document.addEventListener('DOMContentLoaded', () => {
            game.init();
            
            // Добавляем CSS анимации
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideDown {
                    from { transform: translateX(-50%) translateY(-50px); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
                
                .achievement {
                    display: flex;
                    align-items: center;
                    background: rgba(255,255,255,0.05);
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 10px;
                    border-left: 4px solid #f59e0b;
                }
                
                .leaderboard-item {
                    display: flex;
                    align-items: center;
                    background: rgba(255,255,255,0.05);
                    padding: 12px;
                    margin: 8px 0;
                    border-radius: 10px;
                    transition: transform 0.2s;
                }
                
                .leaderboard-item:hover {
                    transform: translateX(5px);
                    background: rgba(255,255,255,0.08);
                }
                
                .rank {
                    width: 36px;
                    height: 36px;
                    background: #6366f1;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    margin-right: 15px;
                    color: white;
                }
                
                .rank-1 { background: linear-gradient(145deg, #fbbf24, #f59e0b); }
                .rank-2 { background: linear-gradient(145deg, #94a3b8, #64748b); }
                .rank-3 { background: linear-gradient(145deg, #a16207, #854d0e); }
                
                .user-name {
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                
                .user-stats {
                    font-size: 14px;
                    opacity: 0.8;
                    display: flex;
                    gap: 15px;
                }
            `;
            document.head.appendChild(style);
        });
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
                    username = COALESCE(?, username),
                    coins = COALESCE(?, coins),
                    power = COALESCE(?, power),
                    autos = COALESCE(?, autos),
                    multiplier = COALESCE(?, multiplier),
                    total_clicks = COALESCE(?, total_clicks),
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                username,
                data.get('coins'),
                data.get('power'),
                data.get('autos'),
                data.get('multiplier'),
                data.get('total_clicks'),
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
        
        # Считаем онлайн игроков
        online = conn.execute('''
            SELECT COUNT(*) as count FROM users 
            WHERE last_active > datetime('now', '-5 minutes')
        ''').fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leaderboard': [dict(row) for row in leaderboard],
            'online': online,
            'timestamp': datetime.now().isoformat()
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

# Информация о сервере
@app.route('/api/info', methods=['GET'])
def server_info():
    """Информация о сервере"""
    try:
        conn = get_db()
        total_players = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        online_players = conn.execute('''
            SELECT COUNT(*) as count FROM users 
            WHERE last_active > datetime('now', '-5 minutes')
        ''').fetchone()['count']
        total_coins = conn.execute('SELECT SUM(coins) as total FROM users').fetchone()['total'] or 0
        conn.close()
        
        return jsonify({
            'status': 'online',
            'total_players': total_players,
            'online_players': online_players,
            'total_coins': total_coins,
            'server_time': datetime.now().isoformat()
        })
    except:
        return jsonify({'status': 'online'})

# Проверка здоровья
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Hamster Empire запущен на порту {port}")
    print(f"📁 Статика в папке: {STATIC_DIR}")
    print(f"🗄️  База данных: {DB_FILE}")
    app.run(host='0.0.0.0', port=port, debug=False)
