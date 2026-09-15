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
        
        // Fetch MCP Sync Metadata if available
        try {
            const mcpResponse = await fetch('data/mcp_sync.json');
            if (mcpResponse.ok) {
                const mcpData = await mcpResponse.json();
                if (mcpData.document_id) {
                    const docBtn = document.querySelector('a[href*="docs.google.com/document/"]');
                    if (docBtn) docBtn.href = `https://docs.google.com/document/d/${mcpData.document_id}/edit`;
                }
                if (mcpData.draft_id) {
                    const draftBtn = document.querySelector('a[href*="mail.google.com/mail/"]');
                    if (draftBtn) draftBtn.href = `https://mail.google.com/mail/u/0/#drafts?compose=${mcpData.draft_id}`;
                }
            }
        } catch (e) {
            console.warn('Could not load MCP sync data', e);
        }
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
    
    const themesList = (data.themes && data.themes.themes) ? data.themes.themes : [];
    
    // Sort themes by review_count descending to get top 3
    const sortedThemes = themesList
        .sort((a, b) => (b.review_count || 0) - (a.review_count || 0))
        .slice(0, 3);
        
    // Extract actions from markdown_pulse
    const markdown = data.markdown_pulse || "";
    const actionRegex = /💡 \*\*Action:\*\* (.*?)(?:\n|$)/g;
    let match;
    const extractedActions = [];
    while ((match = actionRegex.exec(markdown)) !== null) {
        extractedActions.push(match[1].trim());
    }

    sortedThemes.forEach((theme, index) => {
        const clone = themeTemplate.content.cloneNode(true);
        
        const themeName = theme.theme_name || theme.name || "Unknown Theme";
        clone.querySelector('.theme-name').textContent = themeName;
        clone.querySelector('.theme-share').textContent = `${theme.share || 0}% share`;
        clone.querySelector('.theme-mentions').textContent = `${theme.review_count || 0} Mentions`;
        clone.querySelector('.theme-quote').textContent = `"${theme.representative_quote || 'No quote available.'}"`;
        clone.querySelector('.theme-bar').style.width = `${theme.share || 0}%`;
        
        themesContainer.appendChild(clone);
        
        // Save action onto the theme object for the next step
        theme.action = extractedActions[index] || "Review markdown for action details.";
    });

    // 4. Render Actions
    const actionsContainer = document.getElementById('actions-container');
    const actionTemplate = document.getElementById('action-item-template');
    actionsContainer.innerHTML = '';
    
    sortedThemes.forEach(theme => {
        if (theme.action) {
            const clone = actionTemplate.content.cloneNode(true);
            const themeName = theme.theme_name || theme.name || "Unknown Theme";
            clone.querySelector('.action-theme-name').textContent = `ACTION · ${themeName}`;
            clone.querySelector('.action-desc').textContent = theme.action;
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
