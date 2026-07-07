/**
 * CSIC Ocean Particles — Dynamic colorful ocean particle system
 * Canvas-based, zero-dependency, auto-responsive.
 * Usage: new OceanParticles(containerEl, options)
 */

class OceanParticles {
    constructor(container, opts = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) return;
        
        this.opts = Object.assign({
            count: 80,           // particle count
            speedMin: 0.3,       // min speed
            speedMax: 1.2,       // max speed
            sizeMin: 1.5,        // min particle size
            sizeMax: 4,          // max particle size
            opacityMin: 0.15,    // min opacity
            opacityMax: 0.55,    // max opacity
            // Ocean colors: deep blue, cyan, teal, gold, coral
            colors: [
                'rgba(8,145,178,{o})',    // cyan
                'rgba(6,182,212,{o})',     // bright cyan
                'rgba(34,211,238,{o})',    // neon cyan
                'rgba(212,168,67,{o})',    // gold
                'rgba(196,30,58,{o})',     // coral red
                'rgba(46,90,168,{o})',     // navy blue
                'rgba(74,122,204,{o})',    // lighter blue
                'rgba(16,185,129,{o})',    // sea green
            ],
            waveAmplitude: 30,   // wave effect amplitude
            waveFrequency: 0.02, // wave frequency
            flowDirection: 'right', // right / left / both
            zIndex: 1,
        }, opts);

        this.canvas = document.createElement('canvas');
        this.canvas.style.cssText = `position:absolute;inset:0;z-index:${this.opts.zIndex};pointer-events:none;`;
        this.container.style.position = this.container.style.position || 'relative';
        this.container.appendChild(this.canvas);
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.time = 0;
        this.rafId = null;
        this._resizeHandler = this._resize.bind(this);
        
        this._init();
    }

    _init() {
        this._resize();
        window.addEventListener('resize', this._resizeHandler);
        this._spawnParticles();
        this._animate();
    }

    _resize() {
        const rect = this.container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.width = rect.width;
        this.height = rect.height;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    _spawnParticles() {
        const count = Math.floor(this.opts.count * (this.width / 1200));
        this.particles = [];
        for (let i = 0; i < count; i++) {
            this.particles.push(this._createParticle());
        }
    }

    _createParticle(x) {
        const o = this.opts;
        return {
            x: x !== undefined ? x : Math.random() * this.width,
            y: Math.random() * this.height,
            size: o.sizeMin + Math.random() * (o.sizeMax - o.sizeMin),
            speed: o.speedMin + Math.random() * (o.speedMax - o.speedMin),
            opacity: o.opacityMin + Math.random() * (o.opacityMax - o.opacityMin),
            colorIdx: Math.floor(Math.random() * o.colors.length),
            phase: Math.random() * Math.PI * 2,
            drift: (Math.random() - 0.5) * 0.5,
        };
    }

    _animate() {
        this.time += 0.016;
        this.ctx.clearRect(0, 0, this.width, this.height);

        const o = this.opts;
        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];
            
            // Flow movement
            if (o.flowDirection === 'right' || o.flowDirection === 'both') {
                p.x += p.speed * 0.6;
            }
            if (o.flowDirection === 'left' || o.flowDirection === 'both') {
                p.x -= p.speed * 0.3;
            }
            
            // Wave motion
            p.y += Math.sin(this.time * 2 + p.phase) * 0.4 + p.drift;
            
            // Wrap around
            if (p.x > this.width + 20) p.x = -20;
            if (p.x < -20) p.x = this.width + 20;
            if (p.y > this.height + 20) p.y = -20;
            if (p.y < -20) p.y = this.height + 20;
            
            // Glow effect
            const colorStr = o.colors[p.colorIdx].replace('{o}', p.opacity);
            const glowStr = o.colors[p.colorIdx].replace('{o}', p.opacity * 0.3);
            
            // Draw glow
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size * 2.5, 0, Math.PI * 2);
            this.ctx.fillStyle = glowStr;
            this.ctx.fill();
            
            // Draw core
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fillStyle = colorStr;
            this.ctx.fill();
        }

        // Subtle connection lines between close particles
        this.ctx.strokeStyle = 'rgba(34,211,238,0.04)';
        this.ctx.lineWidth = 0.5;
        for (let i = 0; i < this.particles.length; i += 4) {
            for (let j = i + 4; j < this.particles.length; j += 4) {
                const a = this.particles[i], b = this.particles[j];
                const dx = a.x - b.x, dy = a.y - b.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(a.x, a.y);
                    this.ctx.lineTo(b.x, b.y);
                    this.ctx.stroke();
                }
            }
        }

        this.rafId = requestAnimationFrame(() => this._animate());
    }

    refresh() {
        this._resize();
        this._spawnParticles();
    }

    destroy() {
        cancelAnimationFrame(this.rafId);
        window.removeEventListener('resize', this._resizeHandler);
        if (this.canvas.parentNode) this.canvas.parentNode.removeChild(this.canvas);
    }
}

// Make global
window.OceanParticles = OceanParticles;
