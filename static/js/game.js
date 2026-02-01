class CoinClickerGame {
    constructor() {
        this.coins = 0;
        this.gems = 10;
        this.tokens = 0;
        this.totalClicks = 0;
        this.totalEarned = 0;
        this.currentGrade = 0;
        this.gradeProgress = 0;
        
        this.clickPower = 1;
        this.critChance = 0.05;
        this.critMultiplier = 2;
        this.totalMultiplier = 1;
        this.coinsPerSecond = 0;
        
        this.upgrades = {};
        this.autoclickers = {};
        this.buildings = {};
        this.achievements = {};
        this.activeBoosts = {};
        
        this.playerId = null;
        this.username = 'Игрок';
        this.playTime = 0;
        
        this.grades = [
            {id: 0, name: 'BRONZE', bonus: 1.0, icon: '🥉', color: '#cd7f32'},
            {id: 1, name: 'SILVER', bonus: 1.1, icon: '🥈', color: '#c0c0c0'},
            {id: 2, name: 'GOLD', bonus: 1.25, icon: '🥇', color: '#ffd700'},
            {id: 3, name: 'PLATINUM', bonus: 1.5, icon: '🏆', color: '#e5e4e2'},
            {id: 4, name: 'DIAMOND', bonus: 2.0, icon: '💎', color: '#b9f2ff'},
            {id: 5, name: 'EMERALD', bonus: 3.0, icon: '🔮', color: '#50c878'},
            {id: 6, name: 'RUBY', bonus: 5.0, icon: '❤️', color: '#e0115f'},
            {id: 7, name: 'SAPPHIRE', bonus: 9.0, icon: '💠', color: '#0f52ba'},
            {id: 8, name: 'AMETHYST', bonus: 16.0, icon: '💜', color: '#9966cc'},
            {id: 9, name: 'COSMIC', bonus: 31.0, icon: '🌌', color: '#8a2be2'}
        ];
        
        this.autoclickerTypes = [
            {id: 'basic', name: 'Простой робот', baseCPS: 0.1, baseCost: 100, icon: '🤖'},
            {id: 'advanced', name: 'Продвинутый робот', baseCPS: 0.5, baseCost: 500, icon: '🦾'},
            {id: 'farm', name: 'Ферма кликов', baseCPS: 2, baseCost: 2000, icon: '🏭'},
            {id: 'factory', name: 'Фабрика', baseCPS: 10, baseCost: 10000, icon: '🏢'},
            {id: 'ai', name: 'ИИ система', baseCPS: 50, baseCost: 50000, icon: '🧠'}
        ];
        
        this.buildingTypes = [
            {id: 'lemonade', name: 'Лавка лимонада', baseCPS: 0.5, baseCost: 1000, icon: '🍋'},
            {id: 'newspaper', name: 'Газетный киоск', baseCPS: 2, baseCost: 5000, icon: '📰'},
            {id: 'car_wash', name: 'Мойка авто', baseCPS: 10, baseCost: 25000, icon: '🚗'},
            {id: 'pizza', name: 'Пиццерия', baseCPS: 50, baseCost: 100000, icon: '🍕'},
            {id: 'cinema', name: 'Кинотеатр', baseCPS: 200, baseCost: 500000, icon: '🎬'},
            {id: 'bank', name: 'Банк', baseCPS: 1000, baseCost: 2500000, icon: '🏦'},
            {id: 'tech', name: 'Тех компания', baseCPS: 5000, baseCost: 10000000, icon: '💻'}
        ];
        
        this.init();
    }
    
    async init() {
        // Telegram WebApp
        if (window.Telegram && Telegram.WebApp) {
            const tg = Telegram.WebApp;
            tg.expand();
            tg.ready();
            
            this.playerId = tg.initDataUnsafe.user?.id || 'player_' + Date.now() + Math.random().toString(36).substr(2, 9);
            this.username = tg.initDataUnsafe.user?.username || tg.initDataUnsafe.user?.first_name || 'Игрок';
            
            if (tg.colorScheme === 'dark') {
                document.body.classList.add('dark-mode');
            }
        } else {
            this.playerId = 'local_' + Date.now();
        }
        
        await this.loadGame();
        this.setupEventListeners();
        this.startGameLoop();
        this.updateUI();
        this.loadUpgrades();
        this.loadAutoclickers();
        this.loadBuildings();
        this.loadAchievements();
        this.loadGradesInfo();
        this.updateLeaderboard('total');
        
        console.log('🎮 Coin Clicker Master инициализирован!');
    }
    
    async loadGame() {
        try {
            const response = await fetch(`/api/player/${this.playerId}`);
            const data = await response.json();
            
            if (data.coins !== undefined) {
                this.coins = data.coins;
                this.gems = data.gems;
                this.tokens = data.tokens;
                this.totalClicks = data.total_clicks;
                this.totalEarned = data.total_earned;
                this.currentGrade = data.current_grade;
                this.gradeProgress = data.grade_progress;
                
                this.upgrades = data.upgrades || {};
                this.autoclickers = data.autoclickers || {};
                this.buildings = data.buildings || {};
                this.achievements = data.achievements || {};
                this.activeBoosts = data.active_boosts || {};
                
                this.calculateStats();
            }
        } catch (error) {
            console.log('Загрузка сохранения:', error);
        }
        
        const localSave = localStorage.getItem(`coinclicker_${this.playerId}`);
        if (localSave) {
            const localData = JSON.parse(localSave);
            Object.assign(this, localData);
        }
        
        this.saveGame();
    }
    
    saveGame() {
        const saveData = {
            coins: this.coins,
            gems: this.gems,
            tokens: this.tokens,
            totalClicks: this.totalClicks,
            totalEarned: this.totalEarned,
            currentGrade: this.currentGrade,
            gradeProgress: this.gradeProgress,
            clickPower: this.clickPower,
            critChance: this.critChance,
            critMultiplier: this.critMultiplier,
            totalMultiplier: this.totalMultiplier,
            coinsPerSecond: this.coinsPerSecond,
            upgrades: this.upgrades,
            autoclickers: this.autoclickers,
            buildings: this.buildings,
            achievements: this.achievements,
            activeBoosts: this.activeBoosts,
            saveTime: Date.now()
        };
        
        localStorage.setItem(`coinclicker_${this.playerId}`, JSON.stringify(saveData));
        
        const achievementsCompleted = Object.values(this.achievements).filter(a => a.completed).length;
        
        fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                player_id: this.playerId,
                username: this.username,
                coins: this.coins,
                gems: this.gems,
                tokens: this.tokens,
                total_clicks: this.totalClicks,
                total_earned: this.totalEarned,
                current_grade: this.currentGrade,
                grade_progress: this.gradeProgress,
                achievements: this.achievements,
                achievements_completed: achievementsCompleted
            })
        }).catch(console.error);
    }
    
    calculateStats() {
        // Базовый клик
        let baseClick = 1;
        
        // Улучшения клика
        if (this.upgrades.click_power) {
            baseClick *= Math.pow(1.1, this.upgrades.click_power);
        }
        
        this.clickPower = baseClick;
        
        // Критические удары
        let critChance = 0.05;
        let critMultiplier = 2;
        
        if (this.upgrades.crit_chance) {
            critChance += this.upgrades.crit_chance * 0.01;
        }
        
        if (this.upgrades.crit_power) {
            critMultiplier += this.upgrades.crit_power * 0.2;
        }
        
        this.critChance = Math.min(critChance, 0.5);
        this.critMultiplier = critMultiplier;
        
        // Множители
        let multiplier = 1;
        
        // Бонус грейда
        const gradeBonus = this.grades[this.currentGrade].bonus;
        multiplier *= gradeBonus;
        
        // Активные бусты
        Object.values(this.activeBoosts).forEach(boost => {
            multiplier *= boost;
        });
        
        // Улучшения множителя
        if (this.upgrades.multiplier) {
            multiplier *= Math.pow(1.2, this.upgrades.multiplier);
        }
        
        this.totalMultiplier = multiplier;
        
        // Автокликеры
        let cps = 0;
        
        Object.entries(this.autoclickers).forEach(([id, data]) => {
            const clicker = this.autoclickerTypes.find(c => c.id === id);
            if (clicker) {
                cps += clicker.baseCPS * data.quantity * data.level;
            }
        });
        
        // Здания
        Object.entries(this.buildings).forEach(([id, data]) => {
            const building = this.buildingTypes.find(b => b.id === id);
            if (building) {
                cps += building.baseCPS * data.quantity * data.level;
            }
        });
        
        this.coinsPerSecond = cps * this.totalMultiplier;
        
        this.updateAchievements();
    }
    
    clickCoin(event) {
        const isCritical = Math.random() < this.critChance;
        const baseGain = this.clickPower * this.totalMultiplier;
        const gain = isCritical ? baseGain * this.critMultiplier : baseGain;
        
        this.coins += gain;
        this.totalClicks++;
        this.totalEarned += gain;
        
        this.addGradeProgress(gain);
        
        const coin = document.getElementById('mainCoin');
        coin.style.animation = 'coinClick 0.1s';
        setTimeout(() => coin.style.animation = '', 100);
        
        this.createClickEffect(event, isCritical, gain);
        this.showNotification(isCritical ? `💥 КРИТИЧЕСКИЙ УДАР! +${gain.toFixed(2)}` : `+${gain.toFixed(2)}`);
        this.updateUI();
        this.saveGame();
        
        return gain;
    }
    
    addGradeProgress(gain) {
        const currentGradeData = this.grades[this.currentGrade];
        const nextGradeData = this.grades[Math.min(this.currentGrade + 1, this.grades.length - 1)];
        
        const progressPerCoin = 100 / (Math.pow(2, this.currentGrade) * 10000);
        this.gradeProgress += gain * progressPerCoin;
        
        if (this.gradeProgress >= 100 && this.currentGrade < this.grades.length - 1) {
            this.currentGrade++;
            this.gradeProgress = 0;
            this.coins += 1000 * Math.pow(2, this.currentGrade);
            this.gems += this.currentGrade;
            
            this.showNotification(`🎉 Новый грейд: ${nextGradeData.name}! +${(1000 * Math.pow(2, this.currentGrade)).toFixed(0)} монет +${this.currentGrade} 💎`);
        }
    }
    
    async buyUpgrade(upgradeId) {
        const upgradeCosts = {
            'click_power': {coins: 50 * Math.pow(1.2, this.upgrades.click_power || 0)},
            'multiplier': {coins: 200 * Math.pow(1.5, this.upgrades.multiplier || 0)},
            'crit_chance': {coins: 500 * Math.pow(1.3, this.upgrades.crit_chance || 0)},
            'crit_power': {coins: 1000 * Math.pow(1.4, this.upgrades.crit_power || 0)}
        };
        
        const cost = upgradeCosts[upgradeId];
        if (!cost) return false;
        
        if (this.coins >= cost.coins) {
            try {
                const response = await fetch('/api/buy_upgrade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        player_id: this.playerId,
                        upgrade_id: upgradeId,
                        cost_coins: cost.coins,
                        type: 'click'
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    this.coins = result.new_balance.coins;
                    this.upgrades[upgradeId] = (this.upgrades[upgradeId] || 0) + 1;
                    
                    this.calculateStats();
                    this.showNotification('✅ Улучшение куплено!');
                    this.updateUI();
                    this.saveGame();
                    return true;
                }
            } catch (error) {
                console.error('Ошибка покупки:', error);
            }
        } else {
            this.showNotification(`❌ Необходимо ${cost.coins.toFixed(2)} монет!`);
        }
        return false;
    }
    
    async buyAutoclicker(clickerId) {
        const clicker = this.autoclickerTypes.find(c => c.id === clickerId);
        if (!clicker) return false;
        
        const owned = this.autoclickers[clickerId]?.quantity || 0;
        const cost = clicker.baseCost * Math.pow(1.15, owned);
        
        if (this.coins >= cost) {
            try {
                const response = await fetch('/api/buy_upgrade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        player_id: this.playerId,
                        upgrade_id: clickerId,
                        cost_coins: cost,
                        type: 'autoclicker'
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    this.coins = result.new_balance.coins;
                    
                    if (!this.autoclickers[clickerId]) {
                        this.autoclickers[clickerId] = {quantity: 1, level: 1};
                    } else {
                        this.autoclickers[clickerId].quantity++;
                    }
                    
                    this.calculateStats();
                    this.showNotification(`✅ ${clicker.name} куплен!`);
                    this.updateUI();
                    this.saveGame();
                    this.loadAutoclickers();
                    return true;
                }
            } catch (error) {
                console.error('Ошибка покупки:', error);
            }
        } else {
            this.showNotification(`❌ Необходимо ${cost.toFixed(2)} монет!`);
        }
        return false;
    }
    
    async buyBuilding(buildingId) {
        const building = this.buildingTypes.find(b => b.id === buildingId);
        if (!building) return false;
        
        const owned = this.buildings[buildingId]?.quantity || 0;
        const cost = building.baseCost * Math.pow(1.12, owned);
        
        if (this.coins >= cost) {
            try {
                const response = await fetch('/api/buy_upgrade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        player_id: this.playerId,
                        upgrade_id: buildingId,
                        cost_coins: cost,
                        type: 'building'
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    this.coins = result.new_balance.coins;
                    
                    if (!this.buildings[buildingId]) {
                        this.buildings[buildingId] = {quantity: 1, level: 1};
                    } else {
                        this.buildings[buildingId].quantity++;
                    }
                    
                    this.calculateStats();
                    this.showNotification(`✅ ${building.name} построено!`);
                    this.updateUI();
                    this.saveGame();
                    this.loadBuildings();
                    return true;
                }
            } catch (error) {
                console.error('Ошибка покупки:', error);
            }
        } else {
            this.showNotification(`❌ Необходимо ${cost.toFixed(2)} монет!`);
        }
        return false;
    }
    
    async buyBoost(boostId) {
        const boosts = {
            'x2_1h': {gems: 5, multiplier: 2, duration: 3600},
            'x3_30m': {gems: 10, multiplier: 3, duration: 1800},
            'x5_15m': {gems: 20, multiplier: 5, duration: 900}
        };
        
        const boost = boosts[boostId];
        if (!boost || this.gems < boost.gems) {
            this.showNotification(`❌ Необходимо ${boost.gems} 💎`);
            return false;
        }
        
        try {
            const response = await fetch('/api/activate_boost', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    player_id: this.playerId,
                    boost_id: boostId,
                    cost_gems: boost.gems,
                    multiplier: boost.multiplier,
                    duration: boost.duration
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.gems -= boost.gems;
                this.activeBoosts[boostId] = boost.multiplier;
                
                this.calculateStats();
                this.showNotification(`⚡ Буст x${boost.multiplier} активирован!`);
                this.updateUI();
                this.saveGame();
                
                setTimeout(() => {
                    delete this.activeBoosts[boostId];
                    this.calculateStats();
                    this.updateUI();
                    this.saveGame();
                }, boost.duration * 1000);
                
                return true;
            }
        } catch (error) {
            console.error('Ошибка активации буста:', error);
        }
        return false;
    }
    
    async claimDailyReward() {
        try {
            const response = await fetch('/api/claim_daily', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({player_id: this.playerId})
            });
            
            const result = await response.json();
            if (result.success) {
                this.coins += result.reward.coins;
                this.gems += result.reward.gems || 0;
                this.tokens += result.reward.tokens || 0;
                
                this.showNotification(`🎁 Дневная награда: +${result.reward.coins} 🪙 +${result.reward.gems || 0} 💎`);
                this.updateUI();
                this.saveGame();
                this.loadDailyRewards();
                return true;
            }
        } catch (error) {
            console.error('Ошибка получения награды:', error);
        }
        return false;
    }
    
    updateUI() {
        // Обновляем значения
        document.getElementById('coinsValue').textContent = this.formatNumber(this.coins);
        document.getElementById('gemsValue').textContent = this.gems;
        document.getElementById('tokensValue').textContent = this.tokens;
        document.getElementById('cpsValue').textContent = this.formatNumber(this.coinsPerSecond);
        
        document.getElementById('clickPower').textContent = this.formatNumber(this.clickPower);
        document.getElementById('critChance').textContent = `${(this.critChance * 100).toFixed(1)}%`;
        document.getElementById('critMultiplier').textContent = this.critMultiplier.toFixed(1);
        document.getElementById('totalMultiplier').textContent = this.totalMultiplier.toFixed(2);
        
        document.getElementById('totalClicks').textContent = this.formatNumber(this.totalClicks);
        document.getElementById('totalEarned').textContent = this.formatNumber(this.totalEarned);
        
        // Обновляем грейд
        const grade = this.grades[this.currentGrade];
        document.getElementById('gradeBadge').innerHTML = `
            <span class="grade-icon">${grade.icon}</span>
            <span class="grade-name">${grade.name}</span>
        `;
        document.getElementById('gradeBadge').style.borderColor = grade.color;
        
        document.getElementById('gradeProgress').style.width = `${Math.min(this.gradeProgress, 100)}%`;
        document.getElementById('gradePercent').textContent = `${Math.min(this.gradeProgress, 100).toFixed(1)}%`;
    }
    
    createClickEffect(event, isCritical, amount) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.textContent = isCritical ? `💥 ${this.formatNumber(amount)}` : `+${this.formatNumber(amount)}`;
        particle.style.left = (event.clientX - 20) + 'px';
        particle.style.top = (event.clientY - 20) + 'px';
        particle.style.color = isCritical ? '#ff4444' : '#ffd700';
        particle.style.fontSize = isCritical ? '28px' : '24px';
        particle.style.fontWeight = 'bold';
        particle.style.textShadow = `0 0 ${isCritical ? '10px' : '5px'} currentColor`;
        
        document.body.appendChild(particle);
        setTimeout(() => particle.remove(), 1000);
        
        if (isCritical) {
            this.createCriticalEffect(event);
        }
    }
    
    createCriticalEffect(event) {
        for (let i = 0; i < 5; i++) {
            const spark = document.createElement('div');
            spark.className = 'particle';
            spark.innerHTML = '✨';
            spark.style.left = (event.clientX - 10) + 'px';
            spark.style.top = (event.clientY - 10) + 'px';
            spark.style.color = '#ff4444';
            spark.style.fontSize = '20px';
            spark.style.animation = `floatUp 1.5s forwards`;
            
            const angle = (Math.PI * 2 * i) / 5;
            const distance = 100;
            
            spark.style.setProperty('--end-x', `${Math.cos(angle) * distance}px`);
            spark.style.setProperty('--end-y', `${Math.sin(angle) * distance}px`);
            
            const style = document.createElement('style');
            style.textContent = `
                @keyframes criticalFloat {
                    0% { transform: translate(0, 0) scale(1); opacity: 1; }
                    100% { transform: translate(var(--end-x), var(--end-y)) scale(0); opacity: 0; }
                }
            `;
            spark.style.animation = 'criticalFloat 1.5s forwards';
            
            document.head.appendChild(style);
            document.body.appendChild(spark);
            
            setTimeout(() => {
                spark.remove();
                if (document.head.contains(style)) {
                    document.head.removeChild(style);
                }
            }, 1500);
        }
    }
    
    showNotification(text) {
        const notification = document.createElement('div');
        notification.textContent = text;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 15px 30px;
            border-radius: 15px;
            z-index: 1000;
            animation: slideDown 0.3s ease-out;
            border-left: 5px solid #ffd700;
            font-weight: bold;
            font-size: 1.1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
            max-width: 90%;
            text-align: center;
        `;
        
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 2000);
    }
    
    setupEventListeners() {
        const coin = document.getElementById('mainCoin');
        if (coin) {
            coin.addEventListener('click', (e) => this.clickCoin(e));
        }
        
        const claimBtn = document.getElementById('claimDailyBtn');
        if (claimBtn) {
            claimBtn.addEventListener('click', () => this.claimDailyReward());
        }
    }
    
    startGameLoop() {
        // Пассивный доход
        setInterval(() => {
            if (this.coinsPerSecond > 0) {
                const passiveGain = this.coinsPerSecond;
                this.coins += passiveGain;
                this.totalEarned += passiveGain;
                this.addGradeProgress(passiveGain);
                this.updateUI();
                this.saveGame();
            }
        }, 1000);
        
        // Обновление времени игры
        setInterval(() => {
            this.playTime++;
            document.getElementById('playTime').textContent = this.formatTime(this.playTime);
        }, 1000);
        
        // Сохранение каждые 30 секунд
        setInterval(() => this.saveGame(), 30000);
    }
    
    loadUpgrades() {
        const clickUpgrades = [
            {id: 'click_power', name: 'Усилитель клика', desc: '+10% к силе клика', icon: '💪'},
            {id: 'multiplier', name: 'Глобальный множитель', desc: '+20% ко всему доходу', icon: '🌀'},
            {id: 'crit_chance', name: 'Критический шанс', desc: '+1% шанс крита', icon: '🎯'},
            {id: 'crit_power', name: 'Мощность крита', desc: '+0.2 к множителю крита', icon: '💥'}
        ];
        
        const multiplierUpgrades = [
            {id: 'x2_1h', name: 'x2 на 1 час', desc: 'Удваивает доход на 1 час', icon: '⚡', gems: 5},
            {id: 'x3_30m', name: 'x3 на 30 минут', desc: 'Утраивает доход на 30 минут', icon: '⚡⚡', gems: 10},
            {id: 'x5_15m', name: 'x5 на 15 минут', desc: 'x5 доход на 15 минут', icon: '⚡⚡⚡', gems: 20}
        ];
        
        // Загружаем улучшения клика
        const clickGrid = document.getElementById('clickUpgrades');
        if (clickGrid) {
            clickGrid.innerHTML = clickUpgrades.map(upgrade => {
                const level = this.upgrades[upgrade.id] || 0;
                const baseCost = upgrade.id === 'click_power' ? 50 : 
                                upgrade.id === 'multiplier' ? 200 : 
                                upgrade.id === 'crit_chance' ? 500 : 1000;
                const cost = baseCost * Math.pow(upgrade.id === 'click_power' ? 1.2 : 
                                               upgrade.id === 'multiplier' ? 1.5 : 
                                               upgrade.id === 'crit_chance' ? 1.3 : 1.4, level);
                
                return `
                    <div class="upgrade-card" onclick="game.buyUpgrade('${upgrade.id}')">
                        <div class="upgrade-header">
                            <div class="upgrade-icon">${upgrade.icon}</div>
                            <div>
                                <div class="upgrade-name">${upgrade.name}</div>
                                <div class="upgrade-level">Уровень: ${level}</div>
                            </div>
                        </div>
                        <div class="upgrade-desc">${upgrade.desc}</div>
                        <div class="upgrade-cost">${this.formatNumber(cost)} 🪙</div>
                    </div>
                `;
            }).join('');
        }
        
        // Загружаем множители
        const multiGrid = document.getElementById('multiplierUpgrades');
        if (multiGrid) {
            multiGrid.innerHTML = multiplierUpgrades.map(boost => `
                <div class="upgrade-card" onclick="game.buyBoost('${boost.id}')">
                    <div class="upgrade-header">
                        <div class="upgrade-icon">${boost.icon}</div>
                        <div class="upgrade-name">${boost.name}</div>
                    </div>
                    <div class="upgrade-desc">${boost.desc}</div>
                    <div class="upgrade-cost">${boost.gems} 💎</div>
                </div>
            `).join('');
        }
    }
    
    loadAutoclickers() {
        const grid = document.getElementById('clickersGrid');
        if (!grid) return;
        
        grid.innerHTML = this.autoclickerTypes.map(clicker => {
            const data = this.autoclickers[clicker.id] || {quantity: 0, level: 1};
            const owned = data.quantity;
            const cost = clicker.baseCost * Math.pow(1.15, owned);
            
            return `
                <div class="upgrade-card" onclick="game.buyAutoclicker('${clicker.id}')">
                    <div class="upgrade-header">
                        <div class="upgrade-icon">${clicker.icon}</div>
                        <div>
                            <div class="upgrade-name">${clicker.name}</div>
                            <div class="upgrade-level">${owned} шт. | Ур. ${data.level}</div>
                        </div>
                    </div>
                    <div class="upgrade-desc">Производит ${clicker.baseCPS * this.totalMultiplier} монет/сек</div>
                    <div class="upgrade-cost">${this.formatNumber(cost)} 🪙</div>
                </div>
            `;
        }).join('');
    }
    
    loadBuildings() {
        const grid = document.getElementById('buildingsGrid');
        if (!grid) return;
        
        grid.innerHTML = this.buildingTypes.map(building => {
            const data = this.buildings[building.id] || {quantity: 0, level: 1};
            const owned = data.quantity;
            const cost = building.baseCost * Math.pow(1.12, owned);
            
            return `
                <div class="building-card" onclick="game.buyBuilding('${building.id}')">
                    <div class="building-header">
                        <div class="building-icon">${building.icon}</div>
                        <div>
                            <div class="building-name">${building.name}</div>
                            <div class="building-level">${owned} шт. | Ур. ${data.level}</div>
                        </div>
                    </div>
                    <div class="building-desc">Производит ${building.baseCPS * this.totalMultiplier} монет/сек</div>
                    <div class="building-cost">${this.formatNumber(cost)} 🪙</div>
                </div>
            `;
        }).join('');
    }
    
    loadAchievements() {
        const achievements = [
            {id: 'first_click', name: 'Первый шаг', desc: 'Сделать 10 кликов', target: 10, reward: 100},
            {id: 'first_100_coins', name: 'Богач', desc: 'Заработать 100 монет', target: 100, reward: 500},
            {id: 'first_upgrade', name: 'Улучшатель', desc: 'Купить первое улучшение', target: 1, reward: 1000},
            {id: 'first_autoclicker', name: 'Автоматизатор', desc: 'Купить первый автокликер', target: 1, reward: 2000},
            {id: 'grade_1', name: 'Серебряный', desc: 'Достигнуть серебряного грейда', target: 1, reward: 5000},
            {id: 'daily_streak_3', name: 'Постоянный', desc: '3 дня подряд заходить в игру', target: 3, reward: 10000},
            {id: 'millionaire', name: 'Миллионер', desc: 'Заработать 1,000,000 монет', target: 1000000, reward: 50000},
            {id: 'click_master', name: 'Мастер клика', desc: '1000 кликов', target: 1000, reward: 5000}
        ];
        
        const grid = document.getElementById('achievementsGrid');
        if (!grid) return;
        
        grid.innerHTML = achievements.map(ach => {
            const data = this.achievements[ach.id] || {progress: 0, completed: false};
            const progress = Math.min(data.progress || 0, ach.target);
            const percent = (progress / ach.target) * 100;
            
            let progressText = '';
            if (ach.id === 'first_click') progressText = `Кликов: ${progress}/${ach.target}`;
            else if (ach.id === 'first_100_coins') progressText = `Монет: ${this.formatNumber(progress)}/${this.formatNumber(ach.target)}`;
            else if (ach.id === 'first_upgrade') progressText = `Улучшений: ${progress}/${ach.target}`;
            else if (ach.id === 'first_autoclicker') progressText = `Автокликеров: ${progress}/${ach.target}`;
            else if (ach.id === 'grade_1') progressText = `Грейд: ${this.currentGrade >= ach.target ? 'Достигнут' : 'Не достигнут'}`;
            else progressText = `${progress}/${ach.target}`;
            
            return `
                <div class="achievement-card ${data.completed ? 'completed' : ''}">
                    <div class="achievement-header">
                        <div class="achievement-icon">${data.completed ? '🏆' : '🎯'}</div>
                        <div class="achievement-name">${ach.name}</div>
                    </div>
                    <div class="achievement-desc">${ach.desc}</div>
                    <div class="achievement-progress">
                        <div class="achievement-progress-fill" style="width: ${percent}%"></div>
                    </div>
                    <div class="achievement-progress-text">${progressText}</div>
                    <div class="achievement-reward">
                        ${data.completed ? '✅ Получено' : `Награда: ${this.formatNumber(ach.reward)} 🪙`}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateAchievements() {
        const achievementsToUpdate = [
            {id: 'first_click', progress: this.totalClicks, target: 10},
            {id: 'first_100_coins', progress: this.totalEarned, target: 100},
            {id: 'first_upgrade', progress: Object.values(this.upgrades).reduce((a, b) => a + b, 0), target: 1},
            {id: 'first_autoclicker', progress: Object.values(this.autoclickers).reduce((a, b) => a + b.quantity, 0), target: 1},
            {id: 'grade_1', progress: this.currentGrade >= 1 ? 1 : 0, target: 1},
            {id: 'click_master', progress: this.totalClicks, target: 1000}
        ];
        
        achievementsToUpdate.forEach(({id, progress, target}) => {
            if (!this.achievements[id]) {
                this.achievements[id] = {progress: 0, completed: false};
            }
            
            this.achievements[id].progress = Math.max(this.achievements[id].progress, progress);
            
            if (!this.achievements[id].completed && this.achievements[id].progress >= target) {
                this.achievements[id].completed = true;
                this.coins += achievementsToUpdate.find(a => a.id === id)?.reward || 1000;
                this.showNotification(`🏆 Достижение разблокировано! +${(achievementsToUpdate.find(a => a.id === id)?.reward || 1000)} 🪙`);
            }
        });
    }
    
    loadDailyRewards() {
        const track = document.getElementById('rewardsTrack');
        if (!track) return;
        
        const rewards = [
            {day: 1, coins: 100, gems: 1},
            {day: 2, coins: 250, gems: 2},
            {day: 3, coins: 500, gems: 3},
            {day: 4, coins: 1000, gems: 5},
            {day: 5, coins: 2500, gems: 8},
            {day: 6, coins: 5000, gems: 13},
            {day: 7, coins: 10000, gems: 21, tokens: 1}
        ];
        
        track.innerHTML = rewards.map(reward => `
            <div class="reward-day">
                <div class="day-number">${reward.day}</div>
                <div class="day-reward">
                    ${reward.coins} 🪙<br>
                    ${reward.gems} 💎<br>
                    ${reward.tokens ? reward.tokens + ' 🪙' : ''}
                </div>
            </div>
        `).join('');
    }
    
    loadGradesInfo() {
        const track = document.getElementById('gradesTrack');
        if (!track) return;
        
        track.innerHTML = this.grades.map((grade, index) => `
            <div class="grade-item ${index === this.currentGrade ? 'current' : ''} ${index < this.currentGrade ? 'unlocked' : ''}" 
                 style="border-color: ${grade.color}">
                <div class="grade-icon">${grade.icon}</div>
                <div class="grade-name">${grade.name}</div>
                <div class="grade-bonus">+${((grade.bonus - 1) * 100).toFixed(0)}%</div>
            </div>
        `).join('');
        
        const currentGrade = this.grades[this.currentGrade];
        const nextGrade = this.grades[Math.min(this.currentGrade + 1, this.grades.length - 1)];
        
        const benefitsList = document.getElementById('currentBenefits');
        if (benefitsList) {
            benefitsList.innerHTML = `
                <li>Доход: +${((currentGrade.bonus - 1) * 100).toFixed(0)}%</li>
                <li>Бонус к автокликерам: +${(this.currentGrade * 10)}%</li>
                <li>Бонус к зданиям: +${(this.currentGrade * 5)}%</li>
                ${currentGrade.id >= 2 ? '<li>Разблокированы премиум функции</li>' : ''}
                ${currentGrade.id >= 4 ? '<li>Доступ к редким улучшениям</li>' : ''}
                ${currentGrade.id >= 6 ? '<li>Легендарные артефакты</li>' : ''}
                ${currentGrade.id >= 8 ? '<li>Космические достижения</li>' : ''}
            `;
        }
    }
    
    async updateLeaderboard(category) {
        try {
            const response = await fetch(`/api/leaderboard/${category}`);
            const players = await response.json();
            
            const content = document.getElementById('leaderboardContent');
            if (!content) return;
            
            content.innerHTML = players.map((player, index) => `
                <div class="leaderboard-item ${player.player_id === this.playerId ? 'highlight' : ''}">
                    <div class="leaderboard-rank ${index < 3 ? `rank-${index + 1}` : ''}">
                        ${index + 1}
                    </div>
                    <div class="leaderboard-player">
                        <div class="player-name">${player.username} ${player.player_id === this.playerId ? '(Вы)' : ''}</div>
                        <div class="player-stats">
                            ${category === 'total' ? `💎 ${this.formatNumber(player.total_score)}` : ''}
                            ${category === 'coins' ? `💰 ${this.formatNumber(player.coins_score)}` : ''}
                            ${category === 'grade' ? `🏆 ${player.grade_score} грейд` : ''}
                            ${category === 'clicks' ? `👆 ${this.formatNumber(player.total_clicks || 0)}` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Ошибка лидерборда:', error);
        }
    }
    
    formatNumber(num) {
        if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
        if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
        return num.toFixed(2);
    }
    
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

// Глобальный объект игры
const game = new CoinClickerGame();
window.game = game;

// Глобальные функции для кнопок
window.buyUpgrade = (id) => game.buyUpgrade(id);
window.buyAutoclicker = (id) => game.buyAutoclicker(id);
window.buyMultiplier = (id) => game.buyBoost(id);
window.buyCritBoost = () => game.buyUpgrade('crit_chance');
window.doPrestige = () => {}; // Заглушка для престижа

window.updateLeaderboard = (category) => game.updateLeaderboard(category);

// Добавляем стили для анимаций
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-100px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
        
        .leaderboard-item.highlight {
            background: rgba(255, 215, 0, 0.2) !important;
            border-left: 4px solid #ffd700;
        }
        
        .achievement-card.completed {
            border-color: #00ff88;
            background: rgba(0, 255, 136, 0.1);
        }
        
        .grade-item.unlocked {
            opacity: 1;
        }
        
        .grade-item:not(.unlocked):not(.current) {
            opacity: 0.5;
            filter: grayscale(100%);
        }
    `;
    document.head.appendChild(style);
});
