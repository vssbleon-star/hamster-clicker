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
        // Инициализация Telegram WebApp
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.expand();
            tg.ready();
            
            this.userId = tg.initDataUnsafe.user?.id || 'user_' + Math.random().toString(36).substr(2, 9);
            this.username = tg.initDataUnsafe.user?.username || tg.initDataUnsafe.user?.first_name || 'Игрок';
        }
        
        this.loadGame();
        this.setupEventListeners();
        this.startAutoClickers();
    }
    
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
        }
        this.updateDisplay();
    }
    
    saveGame() {
        const data = {
            coins: this.coins,
            power: this.power,
            autos: this.autos,
            multiplier: this.multiplier,
            totalClicks: this.totalClicks
        };
        localStorage.setItem('hamster_save_' + this.userId, JSON.stringify(data));
        
        // Сохраняем на сервер
        this.saveToServer();
    }
    
    async saveToServer() {
        try {
            await fetch('/api/save', {
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
        } catch (error) {
            console.log('Ошибка сохранения на сервере:', error);
        }
    }
    
    clickHamster() {
        const earned = this.power * this.multiplier;
        this.coins += earned;
        this.totalClicks++;
        
        this.updateDisplay();
        this.saveGame();
        
        // Создаем эффект монеты
        this.createCoinEffect(earned);
        
        return earned;
    }
    
    buyUpgrade() {
        const cost = 50 * this.power;
        if (this.coins >= cost) {
            this.coins -= cost;
            this.power += 1;
            this.updateDisplay();
            this.saveGame();
            this.showNotification('💪 Сила увеличена до ' + this.power);
            return true;
        }
        this.showNotification(`Нужно ${cost} монет!`);
        return false;
    }
    
    buyAutoClicker() {
        const cost = 100 + (this.autos * 50);
        if (this.coins >= cost) {
            this.coins -= cost;
            this.autos += 1;
            this.updateDisplay();
            this.saveGame();
            this.showNotification('🤖 +1 авто-кликер!');
            return true;
        }
        this.showNotification(`Нужно ${cost} монет!`);
        return false;
    }
    
    updateDisplay() {
        const coinsEl = document.getElementById('coins');
        const powerEl = document.getElementById('power');
        const autosEl = document.getElementById('autos');
        const upgradeCostEl = document.getElementById('upgradeCost');
        const autoCostEl = document.getElementById('autoCost');
        
        if (coinsEl) coinsEl.textContent = this.coins;
        if (powerEl) powerEl.textContent = this.power;
        if (autosEl) autosEl.textContent = this.autos;
        if (upgradeCostEl) upgradeCostEl.textContent = 50 * this.power;
        if (autoCostEl) autoCostEl.textContent = 100 + (this.autos * 50);
    }
    
    createCoinEffect(amount) {
        const effect = document.createElement('div');
        effect.textContent = `+${amount} 🪙`;
        effect.style.position = 'fixed';
        effect.style.color = '#f59e0b';
        effect.style.fontWeight = 'bold';
        effect.style.pointerEvents = 'none';
        effect.style.zIndex = '1000';
        effect.style.animation = 'coinEffect 1s forwards';
        
        // Случайная позиция
        const x = 50 + Math.random() * 50;
        const y = 50 + Math.random() * 50;
        effect.style.left = x + '%';
        effect.style.top = y + '%';
        
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
            padding: 10px 20px;
            border-radius: 10px;
            z-index: 1000;
            animation: notificationSlide 0.3s;
        `;
        
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 2000);
    }
    
    setupEventListeners() {
        // Клик по хомяку
        const hamsterEl = document.getElementById('hamster');
        if (hamsterEl) {
            hamsterEl.addEventListener('click', (e) => {
                this.clickHamster();
                
                // Анимация клика
                hamsterEl.style.transform = 'scale(0.95)';
                setTimeout(() => hamsterEl.style.transform = 'scale(1)', 100);
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
        // Авто-кликеры каждые 5 секунд
        setInterval(() => {
            if (this.autos > 0) {
                const earned = this.autos * this.multiplier;
                this.coins += earned;
                this.updateDisplay();
                this.saveGame();
                
                if (earned > 0) {
                    this.showNotification(`🤖 Авто: +${earned} 🪙`);
                }
            }
        }, 5000);
    }
}

// Создаем глобальный объект игры
window.hamsterGame = new HamsterGame();

// Запускаем игру когда DOM загружен
document.addEventListener('DOMContentLoaded', () => {
    window.hamsterGame.init();
    
    // Добавляем CSS анимации
    const style = document.createElement('style');
    style.textContent = `
        @keyframes coinEffect {
            0% { opacity: 1; transform: translateY(0) scale(1); }
            100% { opacity: 0; transform: translateY(-100px) scale(1.5); }
        }
        
        @keyframes notificationSlide {
            from { transform: translateX(-50%) translateY(-50px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
});