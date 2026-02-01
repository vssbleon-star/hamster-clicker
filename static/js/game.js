class CosmicClicker {
    constructor() {
        this.stardust = 100.0;
        this.energy = 100.0;
        this.energyCapacity = 100.0;
        this.energyRegen = 1.0;
        this.clickPower = 1.0;
        this.autoMiners = 0;
        this.multiplier = 1.0;
        this.galaxyTier = 0;
        this.starLevel = 1;
        this.experience = 0;
        this.darkMatter = 0;
        this.totalClicks = 0;
        this.artifactsFound = 0;
        
        this.critChance = 0.05;
        this.critMultiplier = 3.0;
        
        this.playerId = null;
        this.username = 'Космический Исследователь';
        this.technologies = {};
        this.artifacts = {};
        this.activeEvents = [];
        
        this.init();
    }
    
    async init() {
        if (window.Telegram && Telegram.WebApp) {
            const tg = Telegram.WebApp;
            tg.expand();
            tg.ready();
            
            this.playerId = tg.initDataUnsafe.user?.id || 'cosmic_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            this.username = tg.initDataUnsafe.user?.username || tg.initDataUnsafe.user?.first_name || this.username;
            
            if (tg.colorScheme === 'dark') {
                document.body.classList.add('dark-theme');
            }
            
            if (tg.HapticFeedback) {
                this.haptic = tg.HapticFeedback;
            }
        } else {
            this.playerId = 'local_' + Date.now();
        }
        
        await this.loadGame();
        this.setupEventListeners();
        this.startGameLoop();
        this.updateUI();
        this.loadTechnologies();
        this.loadArtifacts();
        this.checkEvents();
        this.startParticles();
        
        console.log('🚀 Cosmic Clicker инициализирован!');
    }
    
    async loadGame() {
        try {
            const response = await fetch(`/api/player/${this.playerId}`);
            const data = await response.json();
            
            if (data.stardust) {
                this.stardust = parseFloat(data.stardust);
                this.energy = parseFloat(data.cosmic_energy);
                this.energyCapacity = parseFloat(data.energy_capacity);
                this.energyRegen = parseFloat(data.energy_regen);
                this.clickPower = parseFloat(data.click_power);
                this.autoMiners = parseInt(data.auto_miners);
                this.multiplier = parseFloat(data.multiplier);
                this.galaxyTier = parseInt(data.galaxy_tier);
                this.starLevel = parseInt(data.star_level);
                this.experience = parseFloat(data.experience);
                this.darkMatter = parseFloat(data.dark_matter);
                this.totalClicks = parseInt(data.total_clicks) || 0;
                this.artifactsFound = parseInt(data.artifacts_found) || 0;
                
                if (data.technologies) this.technologies = data.technologies;
                if (data.artifacts) this.artifacts = data.artifacts;
                if (data.active_events) this.activeEvents = data.active_events;
            }
        } catch (error) {
            console.log('Загрузка сохранения:', error);
        }
        
        const localSave = localStorage.getItem(`cosmic_${this.playerId}`);
        if (localSave) {
            const localData = JSON.parse(localSave);
            Object.assign(this, localData);
        }
        
        this.saveGame();
    }
    
    saveGame() {
        const saveData = {
            stardust: this.stardust,
            cosmic_energy: this.energy,
            energy_capacity: this.energyCapacity,
            energy_regen: this.energyRegen,
            click_power: this.clickPower,
            auto_miners: this.autoMiners,
            multiplier: this.multiplier,
            galaxy_tier: this.galaxyTier,
            star_level: this.starLevel,
            experience: this.experience,
            dark_matter: this.darkMatter,
            total_clicks: this.totalClicks,
            artifacts_found: this.artifactsFound,
            save_time: Date.now()
        };
        
        localStorage.setItem(`cosmic_${this.playerId}`, JSON.stringify(saveData));
        
        fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                player_id: this.playerId,
                username: this.username,
                ...saveData
            })
        }).catch(console.error);
    }
    
    clickStar() {
        if (this.energy >= 1) {
            const isCritical = Math.random() < this.critChance;
            const baseGain = this.clickPower * this.multiplier * (1 + this.galaxyTier * 0.25);
            const gain = isCritical ? baseGain * this.critMultiplier : baseGain;
            
            this.stardust += gain;
            this.energy -= 1;
            this.totalClicks++;
            this.addExperience(0.75);
            
            this.createClickEffect(gain, isCritical);
            this.updateUI();
            this.saveGame();
            
            if (this.haptic) {
                this.haptic.impactOccurred(isCritical ? 'heavy' : 'light');
            }
            
            return gain;
        } else {
            this.showMessage('❌ Недостаточно энергии!', '#ff4444');
            return 0;
        }
    }
    
    createClickEffect(amount, isCritical) {
        const starCore = document.getElementById('starCore');
        const rect = starCore.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;
        
        const effect = document.createElement('div');
        effect.innerHTML = isCritical ? '💥' : '✨';
        effect.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            font-size: ${isCritical ? '40px' : '30px'};
            z-index: 1000;
            pointer-events: none;
            animation: ${isCritical ? 'criticalEffect' : 'floatEffect'} 1.5s forwards;
            color: ${isCritical ? '#ff4444' : '#ffd700'};
            text-shadow: 0 0 ${isCritical ? '20px' : '10px'} currentColor;
            filter: drop-shadow(0 0 ${isCritical ? '10px' : '5px'} currentColor);
        `;
        
        if (isCritical) {
            const style = document.createElement('style');
            style.textContent = `
                @keyframes criticalEffect {
                    0% { transform: translate(-50%, -50%) scale(0) rotate(0deg); opacity: 1; }
                    50% { transform: translate(-50%, -50%) scale(3) rotate(180deg); opacity: 0.8; }
                    100% { transform: translate(${Math.random() * 200 - 100}px, ${-150 - Math.random() * 100}px) scale(0) rotate(360deg); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(effect);
        setTimeout(() => effect.remove(), 1500);
        
        if (!isCritical) {
            this.createStardustParticles(x, y, amount);
        }
    }
    
    createStardustParticles(x, y, amount) {
        for (let i = 0; i < Math.min(10, Math.floor(amount / 10)); i++) {
            const particle = document.createElement('div');
            particle.innerHTML = '💎';
            particle.style.cssText = `
                position: fixed;
                left: ${x}px;
                top: ${y}px;
                font-size: 16px;
                z-index: 999;
                pointer-events: none;
                animation: particle${i} 2s forwards;
            `;
            
            const style = document.createElement('style');
            style.textContent = `
                @keyframes particle${i} {
                    0% { transform: translate(0, 0) scale(1) rotate(0deg); opacity: 1; }
                    100% { 
                        transform: translate(${Math.random() * 300 - 150}px, ${Math.random() * 200 + 100}px) 
                                   scale(0) rotate(${Math.random() * 360}deg); 
                        opacity: 0; 
                    }
                }
            `;
            document.head.appendChild(style);
            
            document.body.appendChild(particle);
            setTimeout(() => {
                particle.remove();
                if (document.head.contains(style)) {
                    document.head.removeChild(style);
                }
            }, 2000);
        }
    }
    
    addExperience(amount) {
        this.experience += amount;
        const needed = this.starLevel * 100;
        
        if (this.experience >= needed) {
            this.experience -= needed;
            this.starLevel++;
            this.stardust += this.starLevel * 250;
            this.energyCapacity += 50;
            
            this.showMessage(`🌟 Уровень ${this.starLevel}! +${this.starLevel * 250} звёздной пыли`, '#ffd700');
            
            if (this.starLevel % 5 === 0) {
                this.discoverArtifact();
            }
        }
    }
    
    async discoverArtifact() {
        try {
            const response = await fetch('/api/artifacts/discover', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({player_id: this.playerId})
            });
            
            const result = await response.json();
            if (result.success) {
                this.artifactsFound++;
                this.artifacts[result.artifact.id] = result.artifact.power;
                this.multiplier *= result.artifact.power;
                
                this.showMessage(`🔮 Найден артефакт: ${result.artifact.name}! Множитель x${result.artifact.power}`, '#d9a1ff');
                this.updateUI();
                this.saveGame();
            }
        } catch (error) {
            console.error('Ошибка при обнаружении артефакта:', error);
        }
    }
    
    buyUpgrade(id, cost) {
        if (this.stardust >= cost) {
            this.stardust -= cost;
            
            switch(id) {
                case 'quantum_amplifier':
                    this.clickPower *= 1.15;
                    break;
                case 'energy_core':
                    this.energyCapacity += 100;
                    break;
                case 'stellar_reactor':
                    this.energyRegen *= 1.25;
                    break;
                case 'auto_miner':
                    this.autoMiners++;
                    break;
                case 'multiplier_circuit':
                    this.multiplier *= 1.3;
                    break;
                case 'critical_enhancer':
                    this.critChance += 0.02;
                    this.critMultiplier += 0.5;
                    break;
            }
            
            fetch('/api/upgrade', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    player_id: this.playerId,
                    tech_id: id,
                    cost: cost
                })
            }).catch(console.error);
            
            this.showMessage('✅ Улучшение приобретено!', '#00ff88');
            this.updateUI();
            this.saveGame();
            return true;
        } else {
            this.showMessage(`❌ Необходимо ${cost} звёздной пыли!`, '#ff4444');
            return false;
        }
    }
    
    async ascendGalaxy() {
        const requirement = 1000000 * (this.galaxyTier + 1);
        
        if (this.stardust >= requirement) {
            try {
                const response = await fetch('/api/ascend', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({player_id: this.playerId})
                });
                
                const result = await response.json();
                if (result.success) {
                    const oldTier = this.galaxyTier;
                    this.galaxyTier++;
                    this.stardust = 100;
                    this.energy = 100;
                    this.energyCapacity = 100;
                    this.darkMatter += result.dark_matter_gained;
                    
                    this.showMessage(`🌌 Аскенд в галактику ${this.galaxyTier}! +${result.dark_matter_gained.toFixed(2)} тёмной материи`, '#8a2be2');
                    this.updateUI();
                    this.saveGame();
                }
            } catch (error) {
                console.error('Ошибка аскенда:', error);
            }
        } else {
            this.showMessage(`❌ Необходимо ${requirement.toLocaleString()} звёздной пыли!`, '#ff4444');
        }
    }
    
    updateUI() {
        document.getElementById('stardust').textContent = this.stardust.toFixed(2);
        document.getElementById('energy').textContent = `${this.energy.toFixed(1)}/${this.energyCapacity}`;
        document.getElementById('darkMatter').textContent = this.darkMatter.toFixed(4);
        
        document.getElementById('energyFill').style.width = `${(this.energy / this.energyCapacity) * 100}%`;
        document.getElementById('xpFill').style.width = `${(this.experience / (this.starLevel * 100)) * 100}%`;
        
        document.getElementById('starLevel').textContent = this.starLevel;
        document.getElementById('galaxyTier').textContent = this.galaxyTier;
        document.getElementById('xp').textContent = this.experience.toFixed(1);
        document.getElementById('xpNeeded').textContent = this.starLevel * 100;
        
        const clickGain = this.clickPower * this.multiplier * (1 + this.galaxyTier * 0.25);
        document.getElementById('clickPower').textContent = clickGain.toFixed(2);
        document.getElementById('energyCost').textContent = '1.00';
        document.getElementById('critChance').textContent = `${(this.critChance * 100).toFixed(1)}%`;
        
        const autoIncome = this.autoMiners * 0.75 * this.multiplier;
        document.getElementById('autoIncome').textContent = autoIncome.toFixed(2);
        document.getElementById('minerCount').textContent = `(${this.autoMiners} майнеров)`;
        document.getElementById('stardustPerSecond').textContent = `${autoIncome.toFixed(2)}/сек`;
        
        const galaxyNames = ['Млечный Путь', 'Андромеда', 'Треугольник', 'Сигара', 'Сомбреро'];
        document.getElementById('currentGalaxy').textContent = galaxyNames[this.galaxyTier % galaxyNames.length];
        document.getElementById('nextGalaxy').textContent = galaxyNames[(this.galaxyTier + 1) % galaxyNames.length];
        
        const requirement = 1000000 * (this.galaxyTier + 1);
        document.getElementById('galaxyRequirement').textContent = requirement.toLocaleString();
    }
    
    showMessage(text, color) {
        const message = document.createElement('div');
        message.textContent = text;
        message.style.cssText = `
            position: fixed;
            top: 20%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.85);
            color: ${color};
            padding: 15px 30px;
            border-radius: 15px;
            z-index: 2000;
            font-size: 1.3rem;
            font-weight: bold;
            border-left: 5px solid ${color};
            box-shadow: 0 5px 25px rgba(0,0,0,0.5);
            animation: messageSlide 0.3s ease-out;
            backdrop-filter: blur(10px);
        `;
        
        document.body.appendChild(message);
        setTimeout(() => message.remove(), 2000);
    }
    
    setupEventListeners() {
        const starCore = document.getElementById('starCore');
        if (starCore) {
            starCore.addEventListener('click', (e) => {
                this.clickStar();
            });
        }
        
        const ascendBtn = document.getElementById('ascendGalaxyBtn');
        if (ascendBtn) {
            ascendBtn.addEventListener('click', () => {
                this.ascendGalaxy();
            });
        }
        
        document.querySelectorAll('[data-upgrade]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const upgradeId = e.currentTarget.dataset.upgrade;
                const cost = parseFloat(e.currentTarget.dataset.cost);
                this.buyUpgrade(upgradeId, cost);
            });
        });
    }
    
    startGameLoop() {
        setInterval(() => {
            if (this.energy < this.energyCapacity) {
                this.energy = Math.min(this.energyCapacity, this.energy + this.energyRegen);
            }
            
            if (this.autoMiners > 0) {
                const autoGain = this.autoMiners * 0.75 * this.multiplier;
                this.stardust += autoGain;
            }
            
            this.updateUI();
            this.saveGame();
        }, 1000);
        
        setInterval(() => this.randomEvent(), 300000);
        setInterval(() => this.saveGame(), 30000);
    }
    
    randomEvent() {
        const events = [
            {type: 'cosmic_storm', name: 'Космический шторм', multiplier: 1.5, duration: 120},
            {type: 'quantum_surge', name: 'Квантовый скачок', multiplier: 2.0, duration: 60},
            {type: 'dark_matter_rain', name: 'Дождь тёмной материи', multiplier: 1.0, duration: 180}
        ];
        
        const event = events[Math.floor(Math.random() * events.length)];
        this.activeEvents.push({
            ...event,
            endsAt: Date.now() + event.duration * 1000
        });
        
        this.multiplier *= event.multiplier;
        
        const banner = document.getElementById('eventBanner');
        const timer = document.getElementById('eventTimer');
        const text = document.querySelector('.event-text');
        
        if (banner && timer && text) {
            text.textContent = `${event.name}: +${((event.multiplier - 1) * 100)}% к добыче!`;
            banner.style.display = 'block';
            
            const updateTimer = () => {
                const remaining = Math.max(0, event.duration - (Date.now() - (this.activeEvents[this.activeEvents.length - 1].endsAt - event.duration * 1000)) / 1000);
                const minutes = Math.floor(remaining / 60);
                const seconds = Math.floor(remaining % 60);
                timer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                
                if (remaining > 0) {
                    setTimeout(updateTimer, 1000);
                } else {
                    banner.style.display = 'none';
                    this.multiplier /= event.multiplier;
                    this.activeEvents = this.activeEvents.filter(e => e.endsAt > Date.now());
                }
            };
            
            updateTimer();
        }
        
        this.showMessage(`🌌 ${event.name} начался!`, '#ff00ff');
        this.updateUI();
    }
    
    checkEvents() {
        const now = Date.now();
        this.activeEvents = this.activeEvents.filter(event => {
            if (event.endsAt > now) return true;
            this.multiplier /= event.multiplier;
            return false;
        });
    }
    
    startParticles() {
        setInterval(() => {
            if (Math.random() > 0.7) {
                this.createBackgroundParticle();
            }
        }, 300);
    }
    
    createBackgroundParticle() {
        const particle = document.createElement('div');
        particle.innerHTML = Math.random() > 0.5 ? '✨' : '💫';
        particle.style.cssText = `
            position: fixed;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            font-size: ${Math.random() * 20 + 10}px;
            z-index: 0;
            pointer-events: none;
            opacity: ${Math.random() * 0.3 + 0.1};
            animation: floatParticle ${Math.random() * 10 + 10}s linear infinite;
        `;
        
        document.body.appendChild(particle);
        setTimeout(() => particle.remove(), 15000);
    }
    
    async loadTechnologies() {
        const techs = [
            {id: 'quantum_amplifier', name: 'Квантовый усилитель', desc: '+15% к силе клика', cost: 500, icon: '⚡'},
            {id: 'energy_core', name: 'Энергоядро', desc: '+100 к ёмкости энергии', cost: 1000, icon: '🔋'},
            {id: 'stellar_reactor', name: 'Звёздный реактор', desc: '+25% к регенерации', cost: 2500, icon: '☀️'},
            {id: 'auto_miner', name: 'Авто-майнер', desc: '+0.75 пыли/сек', cost: 5000, icon: '⛏️'},
            {id: 'multiplier_circuit', name: 'Мультипликатор', desc: 'x1.3 ко всей добыче', cost: 15000, icon: '🌀'},
            {id: 'critical_enhancer', name: 'Критический усилитель', desc: '+2% шанс, +0.5 множитель', cost: 30000, icon: '💥'}
        ];
        
        const grid = document.getElementById('upgradesGrid');
        if (grid) {
            grid.innerHTML = techs.map(tech => `
                <div class="upgrade-item" data-upgrade="${tech.id}" data-cost="${tech.cost}">
                    <div style="font-size: 3rem; margin-bottom: 15px;">${tech.icon}</div>
                    <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 10px;">${tech.name}</div>
                    <div style="opacity: 0.9; margin-bottom: 15px;">${tech.desc}</div>
                    <div style="color: #ffd700; font-size: 1.4rem; font-weight: bold;">
                        ${tech.cost.toLocaleString()} 💎
                    </div>
                </div>
            `).join('');
        }
    }
    
    async loadArtifacts() {
        const grid = document.getElementById('artifactsGrid');
        if (grid) {
            const artifacts = Object.entries(this.artifacts).map(([id, power]) => ({
                id, power, 
                name: id.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
            }));
            
            if (artifacts.length === 0) {
                grid.innerHTML = '<div style="text-align: center; padding: 40px; color: #888;">Артефакты ещё не найдены</div>';
            } else {
                grid.innerHTML = artifacts.map(art => `
                    <div class="artifact-card">
                        <div style="font-size: 4rem; margin-bottom: 15px;">🔮</div>
                        <div style="font-size: 1.4rem; font-weight: bold; margin-bottom: 10px;">${art.name}</div>
                        <div style="color: #d9a1ff; font-size: 1.2rem;">Множитель: x${art.power}</div>
                    </div>
                `).join('');
            }
        }
    }
    
    async updateLeaderboard(category = 'stardust') {
        try {
            const response = await fetch(`/api/leaderboard/${category}`);
            const players = await response.json();
            
            const table = document.getElementById('leaderboardTable');
            if (table) {
                table.innerHTML = players.map((player, index) => `
                    <div class="leaderboard-row ${player.player_id === this.playerId ? 'your-row' : ''}">
                        <div class="leaderboard-rank ${index < 3 ? `rank-${index + 1}` : ''}">
                            ${index + 1}
                        </div>
                        <div style="flex: 1;">
                            <div style="font-weight: bold; font-size: 1.2rem;">${player.username}</div>
                            <div style="opacity: 0.8; margin-top: 5px;">
                                ${category === 'stardust' ? `💎 ${parseFloat(player.stardust).toLocaleString()}` : ''}
                                ${category === 'power' ? `⚡ ${parseFloat(player.click_power).toFixed(2)}` : ''}
                                ${category === 'galaxy' ? `🌌 ${player.galaxy_tier}` : ''}
                                ${category === 'artifacts' ? `🔮 ${player.artifacts_found}` : ''}
                                <span style="margin-left: 15px; color: #ffd700;">⭐ ${player.star_level}</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Ошибка загрузки лидерборда:', error);
        }
    }
}

let game = new CosmicClicker();
window.game = game;

window.updateLeaderboard = (category) => game.updateLeaderboard(category);

const style = document.createElement('style');
style.textContent = `
    @keyframes floatEffect {
        0% { transform: translate(-50%, -50%) scale(1) rotate(0deg); opacity: 1; }
        100% { transform: translate(${Math.random() * 100 - 50}px, -150px) scale(0) rotate(180deg); opacity: 0; }
    }
    
    @keyframes messageSlide {
        from { transform: translateX(-50%) translateY(-100px); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
    }
    
    @keyframes floatParticle {
        0% { transform: translateY(100vh) rotate(0deg); }
        100% { transform: translateY(-100px) rotate(360deg); }
    }
    
    .your-row {
        background: rgba(0, 238, 255, 0.2) !important;
        border-left: 5px solid #00eeff;
    }
    
    .dark-theme {
        filter: brightness(0.95) contrast(1.1);
    }
`;
document.head.appendChild(style);
