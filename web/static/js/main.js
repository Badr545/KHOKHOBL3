// ═══════════════════════════════════════════════════════════════════
// ─── KHOKHO BL3 DASHBOARD — JS
// ═══════════════════════════════════════════════════════════════════

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
        const target = document.querySelector(a.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Fade-in animations
const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            e.target.style.opacity = '1';
            e.target.style.transform = 'translateY(0)';
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('.feature-card, .stat-card, .guild-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s, transform 0.5s';
    observer.observe(el);
});

// Copy to clipboard
document.querySelectorAll('code').forEach(code => {
    code.style.cursor = 'pointer';
    code.title = 'Click to copy';
    code.addEventListener('click', () => {
        navigator.clipboard.writeText(code.textContent);
        const orig = code.style.background;
        code.style.background = '#10b981';
        setTimeout(() => code.style.background = orig, 300);
    });
});

console.log('🌐 Khokho Bl3 Dashboard loaded');