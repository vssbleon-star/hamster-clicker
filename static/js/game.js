class HamsterGame {
    constructor() {
        this.coins = 100;
        this.energy = 100;
        this.maxEnergy = 100;
        this.energyRegen = 1;
        this.clickPower = 1;
        this.autos = 0;
        this.multiplier = 1;
        this.prestige = 0;
        this.level = 1;
        this.experience = 0;
        this.totalClicks = 0;
        
        this.userId = null;
        this.username = 'Игрок';
        this.upgrades = {};
        this.achievements = [];
        
        this.init();
    }
    
    async init() {
        // Telegram
        if (window.Telegram && Telegram.WebApp) {
            const tg = Telegram.WebApp;
            tg.expand();
            tg.ready();
            
            this.userId = tg.initDataUnsafe.user?.id || 'user_' + Date.now();
            this.username = tg.initDataUnsafe.user?.username || 
                           tg.initDataUnsafe.user?.first_name || 'Игрок';
            
            if (tg.colorScheme === 'dark') {
                document.body.classList.add('dark-mode');
            }
        }
        
        this.loadGame();
        this.setupEventListeners();
        this.startGameLoop();
        this.updateUI();
        this.loadUpgrades();
        this.loadAchievements();
        this.updateLeaderboard('coins');
        
        // Тест изображений
        this.testImages();
    }
    
    testImages() {
        const images = ['hamster.png', 'coin.png', 'background.png'];
        images.forEach(img => {
            const test = new Image();
            test.src = `/static/images/${img}`;
            test.onload = () => console.log(`✅ ${img} загружен`);
            test.onerror = () => console.error(`❌ ${img} не найден`);
        });
    }
    
    async loadGame() {
        try {
            const res = await fetch(`/api/user/${this.userId}`);
            const data = await res.json();
            
            if (data.coins) {
                this.coins = parseFloat(data.coins);
                this.energy = parseFloat(data.energy);
                this.maxEnergy = parseInt(data.max_energy);
                this.energyRegen = parseFloat(data.energy_regen);
                this.clickPower = parseFloat(data.click_power);
                this.autos = parseInt(data.autos);
                this.multiplier = parseFloat(data.multiplier);
                this.prestige = parseInt(data.prestige);
                this.level = parseInt(data.level);
                this.experience = parseFloat(data.experience);
                this.totalClicks = parseInt(data.total_clicks) || 0;
            }
        } catch (e) {
            console.log('Нет сохранения на сервере');
        }
        
        // Локальное сохранение
        const local = localStorage.getItem(`hamster_${this.userId}`);
        if (local) {
            const data = JSON.parse(local);
            Object.assign(this, data);
        }
        
        this.saveGame();
    }
    
    saveGame() {
        // Локально
        const saveData = {
            coins: this.coins,
            energy: this.energy,
            maxEnergy: this.maxEnergy,
            energyRegen: this.energyRegen,
            clickPower: this.clickPower,
            autos: this.autos,
            multiplier: this.multiplier,
            prestige: this.prestige,
            level: this.level,
            experience: this.experience,
            totalClicks: this.totalClicks,
            saveTime: Date.now()
        };
        
        localStorage.setItem(`hamster_${this.userId}`, JSON.stringify(saveData));
        
        // На сервер
        fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: this.userId,
                username: this.username,
                coins: this.coins,
                energy: this.energy,
                max_energy: this.maxEnergy,
                energy_regen: this.energyRegen,
                click_power: this.clickPower,
                autos: this.autos,
                multiplier: this.multiplier,
                total_clicks: this.totalClicks,
                prestige: this.prestige,
                level: this.level,
                experience: this.experience
            })
        });
    }
    
    click() {
        if (this.energy >= 1) {
            const earned = this.clickPower * this.multiplier * (1 + this.prestige * 0.1);
            this.coins += earned;
            this.energy -= 1;
            this.totalClicks++;
            this.addExperience(0.5);
            
            // Эффект
            this.createEffect(`+${earned.toFixed(2)} 💰`, '#ffd700');
            
            this.updateUI();
            this.saveGame();
            this.checkAchievements();
            
            return earned;
        } else {
            this.createEffect('❌ Нет энергии!', '#ff4444');
            return 0;
        }
    }
    
    addExperience(amount) {
        this.experience += amount;
        const needed = this.level * 100;
        
        if (this.experience >= needed) {
            this.experience -= needed;
            this.level++;
            this.coins += this.level * 100;
            this.createEffect(`🎉 Уровень ${this.level}!`, '#00ff88');
        }
    }
    
    buyUpgrade(id, cost) {
        if (this.coins >= cost) {
            this.coins -= cost;
            
            switch(id) {
                case 'click_power':
                    this.clickPower *= 1.1;
                    break;
                case 'max_energy':
                    this.maxEnergy += 50;
                    break;
                case 'energy_regen':
                    this.energyRegen *= 1.2;
                    break;
                case 'auto_clicker':
                    this.autos++;
                    break;
                case 'multiplier':
                    this.multiplier *= 1.5;
                    break;
            }
            
            this.createEffect(`✅ Улучшение куплено!`, '#00ff88');
            this.updateUI();
            this.saveGame();
            return true;
        } else {
            this.createEffect(`❌ Нужно ${cost} монет!`, '#ff4444');
            return false;
        }
    }
    
    async prestige() {
        if (this.coins >= 1000000) {
            this.prestige++;
            const bonus = this.coins * 0.1;
            this.coins = 100 + bonus;
            this.energy = 100;
            this.maxEnergy = 100;
            this.energyRegen = 1;
            this.clickPower = 1;
            this.autos = 0;
            this.multiplier = 1;
            this.level = 1;
            this.experience = 0;
            
            this.createEffect(`👑 Престиж ${this.prestige}! +${bonus} монет`, '#ffd700');
            this.updateUI();
            this.saveGame();
        } else {
            this.createEffect('❌ Нужно 1,000,000 монет!', '#ff4444');
        }
    }
    
    updateUI() {
        // Основные значения
        document.getElementById('coins').textContent = this.coins.toFixed(2);
        document.getElementById('energy').textContent = 
            `${this.energy.toFixed(1)}/${this.maxEnergy}`;
        document.getElementById('clickPower').textContent = this.clickPower.toFixed(2);
        
        // Бары
        const energyPercent = (this.energy / this.maxEnergy) * 100;
        document.getElementById('energyFill').style.width = energyPercent + '%';
        
        const xpPercent = (this.experience / (this.level * 100)) * 100;
        document.getElementById('levelFill').style.width = xpPercent + '%';
        
        // Тексты
        document.getElementById('level').textContent = this.level;
        document.getElementById('xp').textContent = this.experience.toFixed(1);
        document.getElementById('xpNeeded').textContent = this.level * 100;
        document.getElementById('currentClick').textContent = 
            (this.clickPower * this.multiplier * (1 + this.prestige * 0.1)).toFixed(2);
        document.getElementById('autoIncome').textContent = (this.autos * 0.5).toFixed(2);
        document.getElementById('prestige').textContent = this.prestige;
        document.getElementById('currentPrestige').textContent = this.prestige;
        document.getElementById('prestigeBonus').textContent = (this.prestige * 10) + '%';
        document.getElementById('prestigeRequirement').textContent = '1,000,000';
    }
    
    createEffect(text, color) {
        const effect = document.createElement('div');
        effect.textContent = text;
        effect.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: ${color};
            font-size: 24px;
            font-weight: bold;
            text-shadow: 0 0 10px ${color};
            z-index: 1000;
            pointer-events: none;
            animation: floatUp 1s forwards;
        `;
        
        document.body.appendChild(effect);
        setTimeout(() => effect.remove(), 1000);
    }
    
    setupEventListeners() {
        // Клик хомяка
        const hamster = document.getElementById('hamsterBtn');
        if (hamster) {
            hamster.addEventListener('click', (e) => {
                const earned = this.click();
                
                // Анимация
                hamster.style.transform = 'scale(0.95)';
                setTimeout(() => hamster.style.transform = 'scale(1)', 100);
                
                // Вибро
                if (window.Telegram && Telegram.WebApp?.HapticFeedback) {
                    Telegram.WebApp.HapticFeedback.impactOccurred('light');
                }
                
                // Частицы
                this.createParticles(e.clientX, e.clientY);
            });
        }
    }
    
    createParticles(x, y) {
        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.innerHTML = '💰';
            particle.style.cssText = `
                position: fixed;
                left: ${x}px;
                top: ${y}px;
                font-size: 20px;
                z-index: 999;
                pointer-events: none;
                animation: particle${i} 1s forwards;
            `;
            
            // Динамический CSS для анимации
            const style = document.createElement('style');
            style.textContent = `
                @keyframes particle${i} {
                    0% { transform: translate(0, 0) scale(1); opacity: 1; }
                    100% { 
                        transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * -100 - 50}px) scale(0); 
                        opacity: 0; 
                    }
                }
            `;
            document.head.appendChild(style);
            
            document.body.appendChild(particle);
            setTimeout(() => particle.remove(), 1000);
        }
    }
    
    startGameLoop() {
        // Восстановление энергии
        setInterval(() => {
            if (this.energy < this.maxEnergy) {
                this.energy = Math.min(this.maxEnergy, this.energy + this.energyRegen);
                this.updateUI();
            }
        }, 1000);
        
        // Авто-кликеры
        setInterval(() => {
            if (this.autos > 0) {
                const earned = this.autos * 0.5 * this.multiplier;
                this.coins += earned;
                this.updateUI();
                this.saveGame();
            }
        }, 1000);
        
        // Сохранение каждые 30 секунд
        setInterval(() => this.saveGame(), 30000);
    }
    
    async loadUpgrades() {
        const upgrades = [
            {id: 'click_power', name: 'Усиление', desc: '+10% силы', cost: 50, icon: '💪'},
            {id: 'max_energy', name: 'Энергия', desc: '+50 энергии', cost: 100, icon: '⚡'},
            {id: 'energy_regen', name: 'Реген', desc: '+20% восстановления', cost: 200, icon: '🔄'},
            {id: 'auto_clicker', name: 'Авто-кликер', desc: '+0.5 монет/сек', cost: 500, icon: '🤖'},
            {id: 'multiplier', name: 'Множитель', desc: 'x1.5 доход', cost: 1000, icon: '🚀'}
        ];
        
        const grid = document.getElementById('upgradesGrid');
        if (!grid) return;
        
        grid.innerHTML = upgrades.map(up => `
            <div class="upgrade-item" onclick="game.buyUpgrade('${up.id}', ${up.cost})">
                <div class="upgrade-icon">${up.icon}</div>
                <div class="upgrade-name">${up.name}</div>
                <div class="upgrade-desc">${up.desc}</div>
                <div class="upgrade-cost">${up.cost} 💰</div>
            </div>
        `).join('');
    }
    
    async loadAchievements() {
        try {
            const res = await fetch(`/api/achievements/${this.userId}`);
            this.achievements = await res.json();
            
            const grid = document.getElementById('achievementsGrid');
            if (!grid) return;
            
            grid.innerHTML = this.achievements.map(ach => `
                <div class="achievement-item ${ach.unlocked ? 'unlocked' : ''}">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🏆</div>
                    <div style="font-weight: bold; margin-bottom: 5px;">${ach.name}</div>
                    <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 5px;">${ach.description}</div>
                    <div style="font-size: 0.8rem;">
                        Прогресс: ${ach.progress || 0}/${ach.target}
                        ${ach.unlocked ? '<br>✅ Выполнено!' : ''}
                    </div>
                </div>
            `).join('');
        } catch (e) {
            console.error('Ошибка загрузки достижений:', e);
        }
    }
    
    checkAchievements() {
        // Проверяем выполненные достижения
        this.achievements.forEach(ach => {
            if (!ach.unlocked) {
                let progress = 0;
                
                switch(ach.achievement_id) {
                    case 'first_click':
                        progress = this.totalClicks;
                        break;
                    case '100_coins':
                        progress = this.coins;
                        break;
                    case 'max_energy':
                        progress = this.maxEnergy;
                        break;
                }
                
                if (progress >= ach.target) {
                    this.createEffect(`🏆 ${ach.name} разблокировано!`, '#ffd700');
                }
            }
        });
    }
    
    async updateLeaderboard(type = 'coins') {
        try {
            const res = await fetch(`/api/leaderboard/${type}`);
            const players = await res.json();
            
            const content = document.getElementById('leaderboardContent');
            if (!content) return;
            
            content.innerHTML = players.map((p, i) => `
                <div class="leaderboard-item ${p.user_id === this.userId ? 'you' : ''}">
                    <div class="rank ${i < 3 ? `rank-${i+1}` : ''}">${i + 1}</div>
                    <div style="flex: 1;">
                        <div style="font-weight: bold;">${p.username}</div>
                        <div style="font-size: 0.9rem; opacity: 0.8;">
                            ${type === 'coins' ? `💰 ${p.coins}` : ''}
                            ${type === 'power' ? `💪 ${p.click_power}` : ''}
                            ${type === 'prestige' ? `👑 ${p.prestige}` : ''}
                            ${type === 'level' ? `⭐ ${p.level}` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            console.error('Ошибка загрузки лидерборда:', e);
        }
    }
}

// Инициализация игры
let game;
document.addEventListener('DOMContentLoaded', () => {
    game = new HamsterGame();
    window.game = game;
    
    // CSS для анимаций
    const style = document.createElement('style');
    style.textContent = `
        @keyframes floatUp {
            0% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
            100% { opacity: 0; transform: translate(-50%, -100px) scale(1.5); }
        }
        
        .dark-mode {
            filter: brightness(0.9);
        }
    `;
    document.head.appendChild(style);
});

// Глобальные функции
function showTab(tab) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tab).classList.add('active');
    event.target.classList.add('active');
    
    if (tab === 'leaderboard') {
        game.updateLeaderboard('coins');
    }
}

function showLeaderboard(type) {
    document.querySelectorAll('.lb-tab').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    game.updateLeaderboard(type);
}
