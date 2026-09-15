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
            `<div class="loading" style="color: var(--critical);">Failed to load pulse data. Is latest_pulse.json generated?</div>`;
    }
}

function renderDashboard(data) {
    // 1. Render Metadata
    document.getElementById('date-range').textContent = data.metadata.date_range || 'Unknown Range';
    
    // Animate KPI numbers
    animateValue('kpi-total', 0, data.metadata.total_reviews || 0, 1000);
    document.getElementById('kpi-rating').textContent = data.metadata.average_rating || '0.0';

    // 2. Render Themes & Quotes
    const themesContainer = document.getElementById('themes-container');
    const themeTemplate = document.getElementById('theme-card-template');
    themesContainer.innerHTML = ''; // Clear loading text
    
    // Sort themes by count descending to get top 3
    const sortedThemes = Object.entries(data.themes || {})
        .sort((a, b) => (b[1].count || 0) - (a[1].count || 0))
        .slice(0, 3);
        
    sortedThemes.forEach(([themeName, themeData]) => {
        const clone = themeTemplate.content.cloneNode(true);
        
        clone.querySelector('.theme-name').textContent = themeName;
        clone.querySelector('.theme-count').textContent = `${themeData.count || 0} REVIEWS`;
        clone.querySelector('.quote-text').textContent = `"${themeData.quote || 'No quote available.'}"`;
        
        themesContainer.appendChild(clone);
    });

    // 3. Render Actions
    const actionsContainer = document.getElementById('actions-container');
    const actionTemplate = document.getElementById('action-item-template');
    actionsContainer.innerHTML = '';
    
    sortedThemes.forEach(([themeName, themeData]) => {
        if (themeData.action) {
            const clone = actionTemplate.content.cloneNode(true);
            clone.querySelector('.action-text').innerHTML = `<strong>${themeName}:</strong> ${themeData.action}`;
            actionsContainer.appendChild(clone);
        }
    });
}

function animateValue(id, start, end, duration) {
    if (start === end) return;
    const obj = document.getElementById(id);
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}
