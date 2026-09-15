document.addEventListener('DOMContentLoaded', () => {
    fetchPulseData();
});

async function fetchPulseData() {
    try {
        const response = await fetch('data/latest_pulse.json');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        renderDashboard(data);
    } catch (error) {
        console.error('Error fetching pulse data:', error);
        document.getElementById('themes-container').innerHTML = 
            `<div style="color: var(--error); padding: 1rem;">Failed to load pulse data. Is latest_pulse.json generated?</div>`;
    }
}

function renderDashboard(data) {
    const meta = data.metadata || {};
    const csat = meta.csat || { positive: 0, neutral: 0, negative: 0 };
    
    // 1. Render Metadata & KPIs
    const dateRangeStr = meta.date_range ? `(${meta.date_range})` : '';
    document.getElementById('header-week-date').textContent = `Week ${meta.week_number || '--'} ${dateRangeStr}`;
    
    animateValue('kpi-reviews-total', 0, meta.total_reviews || 0, 1000);
    document.getElementById('kpi-store-rating').textContent = meta.average_rating || '0.0';
    
    document.getElementById('kpi-csat-pos-percent').textContent = `${csat.positive}%`;
    document.getElementById('kpi-csat-neg').textContent = `Neg: ${csat.negative}%`;
    document.getElementById('kpi-csat-neu').textContent = `Neu: ${csat.neutral}%`;
    document.getElementById('kpi-csat-pos').textContent = `Pos: ${csat.positive}%`;
    
    // 2. Render Executive Synthesis
    document.getElementById('executive-synthesis-text').textContent = data.executive_synthesis || 'No executive synthesis available.';

    // 3. Render Themes & Quotes
    const themesContainer = document.getElementById('themes-container');
    const themeTemplate = document.getElementById('theme-card-template');
    themesContainer.innerHTML = '';
    
    // Sort themes by count descending to get top 3
    const sortedThemes = Object.entries(data.themes || {})
        .sort((a, b) => (b[1].count || 0) - (a[1].count || 0))
        .slice(0, 3);
        
    sortedThemes.forEach(([themeName, themeData]) => {
        const clone = themeTemplate.content.cloneNode(true);
        
        clone.querySelector('.theme-name').textContent = themeName;
        clone.querySelector('.theme-share').textContent = `${themeData.share || 0}% share`;
        clone.querySelector('.theme-mentions').textContent = `${themeData.count || 0} Mentions`;
        clone.querySelector('.theme-quote').textContent = `"${themeData.quote || 'No quote available.'}"`;
        clone.querySelector('.theme-bar').style.width = `${themeData.share || 0}%`;
        
        themesContainer.appendChild(clone);
    });

    // 4. Render Actions
    const actionsContainer = document.getElementById('actions-container');
    const actionTemplate = document.getElementById('action-item-template');
    actionsContainer.innerHTML = '';
    
    sortedThemes.forEach(([themeName, themeData]) => {
        if (themeData.action) {
            const clone = actionTemplate.content.cloneNode(true);
            clone.querySelector('.action-theme-name').textContent = `ACTION · ${themeName}`;
            clone.querySelector('.action-desc').textContent = themeData.action;
            actionsContainer.appendChild(clone);
        }
    });
}

function animateValue(id, start, end, duration) {
    if (start === end) return;
    const obj = document.getElementById(id);
    if (!obj) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            obj.innerHTML = end; // Ensure final value is exact
        }
    };
    window.requestAnimationFrame(step);
}
