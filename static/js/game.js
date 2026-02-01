// Основные функции игры
class HamsterGame {
    constructor() {
        this.coins = 100;
        this.power = 1;
        this.autos = 0;
        this.multiplier = 1;
        this.totalClicks = 0;
        this.userId = null;
        this.username = 'Игрок';
    }
    
    init() {
        console.log('Инициализация игры...');
        
        // Telegram WebApp
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.expand();
            tg.ready();
            
            this.userId = tg.initDataUnsafe.user?.id || 'user_' + Math.random().toString(36).substr(2, 9);
            this.username = tg.initDataUnsafe.user?.username || tg.initDataUnsafe.user?.first_name || 'Игрок';
            
            console.log('Telegram WebApp инициализирован:', this.userId, this.username);
        }
        
        this.loadGame();
        this.setupEventListeners();
        this.startAutoClickers();
        this.updateDisplay();
        
        // Проверяем изображение хомяка
        this.checkHamsterImage();
    }
    
    checkHamsterImage() {
        const hamsterImg = document.getElementById('hamsterImage');
        if (!hamsterImg) return;
        
        hamsterImg.onload = () => {
            console.log('Изображение хомяка загружено');
            document.getElementById('hamsterFace').style.display = 'none';
            hamsterImg.style.display = 'block';
        };
        
        hamsterImg.onerror = () => {
            console.log('Изображение не найдено, показываем графическое лицо');
            hamsterImg.style.display = 'none';
            document.getElementById('hamsterFace').style.display = 'block';
        };
        
        // Проверяем загружено ли изображение
        if (hamsterImg.complete) {
            if (hamsterImg.naturalWidth > 0) {
                hamsterImg.onload();
            } else {
                hamsterImg.onerror();
            }
        }
    }
    
    loadGame() {
        // Загрузка из localStorage
        const saved = localStorage.getItem('hamster_save');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                this.coins = data.coins || 100;
                this.power = data.power || 1;
                this.autos = data.autos || 0;
                this.multiplier = data.multiplier || 1;
                this.totalClicks = data.totalClicks || 0;
                console.log('Игра загружена из сохранения');
            } catch (e) {
                console.error('Ошибка загрузки сохранения:', e);
            }
        }
    }
    
    saveGame() {
        const data = {
            coins: this.coins,
            power: this.power,
            autos: this.autos,
            multiplier: this.multiplier,
            totalClicks: this.totalClicks,
            saveTime: Date.now()
        };
        
        localStorage.setItem('hamster_save', JSON.stringify(data));
        console.log('Игра сохранена');
        
        // Сохраняем на сервер если есть userId
        if (this.userId) {
            this.saveToServer();
        }
    }
    
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
            
            const result = await response.json();
            console.log('Сохранено на сервере:', result);
        } catch (error) {
            console.error('Ошибка сохранения на сервере:', error);
        }
    }
    
    clickHamster(event) {
        const earned = this.power * this.multiplier;
        this.coins += earned;
        this.totalClicks++;
        
        // Анимация
        const hamster = document.getElementById('hamsterBtn');
        if (hamster) {
            hamster.style.transform = 'scale(0.95)';
            setTimeout(() => hamster.style.transform = 'scale(1)', 100);
        }
        
        // Создаем эффект
        if (event) {
            this.createEffect(event.clientX, event.clientY, `+${earned} 🪙`, '#f59e0b');
        }
        
        this.updateDisplay();
        this.saveGame();
        
        return earned;
    }
    
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
    }
    
    buyAutoClicker() {
        const cost = 100 + (this.autos * 50);
        if (this.coins >= cost) {
            this.coins -= cost;
            this.autos += 1;
            this.updateDisplay();
            this.saveGame();
            this.showNotification(`🤖 Авто-кликер #${this.autos}!`);
            return true;
        }
        this.showNotification(`❌ Нужно ${cost} монет!`);
        return false;
    }
    
    updateDisplay() {
        const elements = {
            coins: document.getElementById('coins'),
            power: document.getElementById('power'),
            autos: document.getElementById('autos'),
            multiplier: document.getElementById('multiplier'),
            upgradeCost: document.getElementById('upgradeCost'),
            autoCost: document.getElementById('autoCost')
        };
        
        for (const [id, element] of Object.entries(elements)) {
            if (element) {
                if (id === 'coins') element.textContent = this.coins;
                else if (id === 'power') element.textContent = this.power;
                else if (id === 'autos') element.textContent = this.autos;
                else if (id === 'multiplier') element.textContent = this.multiplier + 'x';
                else if (id === 'upgradeCost') element.textContent = 50 * this.power;
                else if (id === 'autoCost') element.textContent = 100 + (this.autos * 50);
            }
        }
    }
    
    createEffect(x, y, text, color) {
        const effect = document.createElement('div');
        effect.textContent = text;
        effect.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            color: ${color};
            font-weight: bold;
            font-size: 18px;
            z-index: 1000;
            pointer-events: none;
            animation: floatUp 1s forwards;
            transform: translate(-50%, -50%);
        `;
        
        document.body.appendChild(effect);
        setTimeout(() => effect.remove(), 1000);
    }
    
    showNotification(text) {
        const notification = document.createElement('div');
        notification.textContent = text;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
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
    }
    
    setupEventListeners() {
        // Клик по хомяку
        const hamsterEl = document.getElementById('hamsterBtn');
        if (hamsterEl) {
            hamsterEl.addEventListener('click', (e) => {
                this.clickHamster(e);
                
                // Вибрация если доступна
                if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
                    window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
                }
            });
        }
        
        // Кнопки улучшений
        const upgradeBtn = document.querySelector('.btn.upgrade');
        if (upgradeBtn) {
            upgradeBtn.addEventListener('click', () => this.buyUpgrade());
        }
        
        const autoBtn = document.querySelector('.btn.auto');
        if (autoBtn) {
            autoBtn.addEventListener('click', () => this.buyAutoClicker());
        }
    }
    
    startAutoClickers() {
        // Авто-кликеры каждые 3 секунды
        setInterval(() => {
            if (this.autos > 0) {
                const earned = this.autos * this.multiplier;
                if (earned > 0) {
                    this.coins += earned;
                    this.updateDisplay();
                    this.saveGame();
                    
                    // Случайный эффект
                    if (Math.random() > 0.7) {
                        const x = 50 + Math.random() * 50;
                        const y = 50 + Math.random() * 50;
                        this.createEffect(
                            window.innerWidth * (x / 100),
                            window.innerHeight * (y / 100),
                            `🤖 +${earned}`,
                            '#9b59b6'
                        );
                    }
                }
            }
        }, 3000);
    }
}

// Создаем глобальный объект игры
window.hamsterGame = new HamsterGame();

// Запускаем игру когда DOM загружен
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM загружен, запускаем игру...');
    window.hamsterGame.init();
    
    // Добавляем CSS анимации
    const style = document.createElement('style');
    style.textContent = `
        @keyframes floatUp {
            0% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
            100% { opacity: 0; transform: translate(-50%, -100px) scale(1.5); }
        }
        
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-50px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
});
