/* ==========================================================================
   RecAI Hub - Application logic controller (Vanilla JS)
   ========================================================================== */

// Application State
let catalogItems = [];
let userRatings = {};
let activeAlgorithm = 'content';
let searchQuery = '';
let activeTypeFilter = 'all';
let selectedGenres = new Set();

// Mock User Presets (Must match backend definitions for visual sync)
const PROFILE_PRESETS = {
    fresh: {},
    scifi: { "m1": 5, "m2": 5, "b1": 5, "b2": 4, "b4": 1, "m5": 2 },
    romance: { "m5": 5, "m6": 5, "b4": 5, "b3": 4, "m2": 2, "m4": 1 },
    thriller: { "b6": 5, "m4": 5, "m2": 4, "m7": 5, "m5": 1, "m3": 4 },
    fantasy: { "b5": 5, "m8": 5, "b1": 4, "m1": 4, "b4": 2, "m6": 2 },
    nonfiction: { "b8": 5, "b7": 5, "b3": 4, "m3": 4, "m2": 3, "m6": 3 }
};

// DOM Elements
const catalogGrid = document.getElementById('catalogGrid');
const catalogCountBadge = document.getElementById('catalogCount');
const searchInput = document.getElementById('catalogSearch');
const filterTabs = document.querySelectorAll('.filter-tab');
const genreFilterContainer = document.getElementById('genreFilterContainer');
const algoTabs = document.querySelectorAll('.algo-tab');
const recResultsList = document.getElementById('recResultsList');
const profileSelect = document.getElementById('profileSelect');
const resetRatingsBtn = document.getElementById('resetRatingsBtn');
const xaiSummary = document.getElementById('xaiSummary');
const xaiVisualization = document.getElementById('xaiVisualization');
const xaiConsoleLogs = document.getElementById('xaiConsoleLogs');
const addItemForm = document.getElementById('addItemForm');
const algorithmDesc = document.getElementById('algorithmDesc');

// Initialize Website
document.addEventListener('DOMContentLoaded', () => {
    fetchCatalog();
    setupEventListeners();
});

// Setup Events
function setupEventListeners() {
    // Search
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase();
        renderCatalog();
    });

    // Content Type Filter tabs (All, Movie, Book)
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeTypeFilter = tab.dataset.filter;
            renderCatalog();
        });
    });

    // Recommendation Algorithm Tab switch
    algoTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            algoTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeAlgorithm = tab.dataset.algo;
            
            // Update explanation description
            if (activeAlgorithm === 'content') {
                algorithmDesc.textContent = "Using TF-IDF and Cosine Similarity on item genres and metadata descriptions to find items matching your rated items.";
            } else {
                algorithmDesc.textContent = "Using Pearson Correlation to compare your rating vectors with 5 peer user personas. Recommends items similar profiles liked.";
            }
            
            fetchRecommendations();
        });
    });

    // Profile Loader
    profileSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        userRatings = { ...PROFILE_PRESETS[val] };
        renderCatalog();
        fetchRecommendations();
    });

    // Reset button
    resetRatingsBtn.addEventListener('click', () => {
        userRatings = {};
        profileSelect.value = 'fresh';
        renderCatalog();
        fetchRecommendations();
    });

    // Add Custom Item Form
    addItemForm.addEventListener('submit', handleAddItemSubmit);
}

// Fetch Items from Backend
async function fetchCatalog() {
    try {
        const response = await fetch('/api/items');
        if (!response.ok) throw new Error("Could not load catalog");
        catalogItems = await response.ok ? await response.json() : [];
        
        buildGenreFilterList();
        renderCatalog();
        fetchRecommendations();
    } catch (err) {
        console.error(err);
        catalogGrid.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>Failed to connect to Python backend server.</p></div>`;
    }
}

// Dynamically generate genre list filters
function buildGenreFilterList() {
    const genresSet = new Set();
    catalogItems.forEach(item => {
        item.genres.forEach(g => genresSet.add(g));
    });
    
    genreFilterContainer.innerHTML = '';
    genresSet.forEach(genre => {
        const btn = document.createElement('button');
        btn.className = 'genre-tag-btn';
        btn.textContent = genre;
        btn.addEventListener('click', () => {
            if (selectedGenres.has(genre)) {
                selectedGenres.delete(genre);
                btn.classList.remove('active');
            } else {
                selectedGenres.add(genre);
                btn.classList.add('active');
            }
            renderCatalog();
        });
        genreFilterContainer.appendChild(btn);
    });
}

// Render Catalog Grid
function renderCatalog() {
    catalogGrid.innerHTML = '';
    
    // Filter logic
    const filtered = catalogItems.filter(item => {
        // Search term matches Title, Director, or Description
        const matchesSearch = item.title.toLowerCase().includes(searchQuery) ||
                             item.author_director.toLowerCase().includes(searchQuery) ||
                             item.description.toLowerCase().includes(searchQuery) ||
                             item.genres.some(g => g.toLowerCase().includes(searchQuery));
                             
        // Type filter matches
        const matchesType = activeTypeFilter === 'all' || item.type === activeTypeFilter;
        
        // Genres matches (OR logic if multiple selected)
        const matchesGenres = selectedGenres.size === 0 || 
                              item.genres.some(g => selectedGenres.has(g));
                              
        return matchesSearch && matchesType && matchesGenres;
    });
    
    catalogCountBadge.textContent = `${filtered.length} Items`;
    
    if (filtered.length === 0) {
        catalogGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-icon">🔍</div>
                <p>No catalog items found matching your filters.</p>
            </div>
        `;
        return;
    }
    
    filtered.forEach(item => {
        const card = document.createElement('article');
        card.className = 'item-card';
        card.id = `card-${item.id}`;
        
        const typeClass = item.type === 'Movie' ? 'cover-movie' : 'cover-book';
        const typeIcon = item.type === 'Movie' ? '🎬' : '📚';
        const genresHTML = item.genres.map(g => `<span class="card-genre">${g}</span>`).join('');
        
        // Star interactive HTML
        let starsHTML = '';
        const currentVal = userRatings[item.id] || 0;
        // 5 to 1 descending for the reverse flex layout
        for (let i = 5; i >= 1; i--) {
            const isActive = i <= currentVal ? 'active' : '';
            starsHTML += `
                <span class="star-input ${isActive}" 
                      data-id="${item.id}" 
                      data-value="${i}" 
                      title="Rate ${i} Stars">★</span>
            `;
        }
        
        card.innerHTML = `
            <div class="card-cover ${typeClass}">
                <span class="card-type-icon">${typeIcon}</span>
                <span>${item.type}</span>
            </div>
            <div class="card-body">
                <h3 class="card-title" title="${item.title}">${item.title}</h3>
                <p class="card-subtitle">${item.author_director} (${item.year})</p>
                <p class="card-desc" title="${item.description}">${item.description}</p>
                <div class="card-genres">
                    ${genresHTML}
                </div>
                <div class="card-rating-row">
                    <span class="avg-rating">
                        <span class="avg-star">★</span> ${item.rating_avg.toFixed(1)}
                    </span>
                    <div class="interactive-stars">
                        ${starsHTML}
                    </div>
                </div>
            </div>
        `;
        
        catalogGrid.appendChild(card);
    });
    
    // Bind star listeners
    document.querySelectorAll('.star-input').forEach(star => {
        star.addEventListener('click', (e) => {
            const itemId = star.dataset.id;
            const ratingValue = parseInt(star.dataset.value);
            
            // Toggle rating: if clicked the same rating, delete it; otherwise update
            if (userRatings[itemId] === ratingValue) {
                delete userRatings[itemId];
            } else {
                userRatings[itemId] = ratingValue;
            }
            
            // Sync with select dropdown header
            profileSelect.value = 'fresh';
            
            renderCatalog();
            fetchRecommendations();
        });
    });
}

// Fetch Recommendations from Python Server
async function fetchRecommendations() {
    // Show loading shimmers
    recResultsList.innerHTML = `
        <div class="loading-shimmer" style="height:80px; margin-bottom:10px;"></div>
        <div class="loading-shimmer" style="height:80px; margin-bottom:10px;"></div>
        <div class="loading-shimmer" style="height:80px;"></div>
    `;
    
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ratings: userRatings,
                algorithm: activeAlgorithm
            })
        });
        
        if (!response.ok) throw new Error("Recommendation endpoint failed");
        
        const data = await response.json();
        renderRecommendations(data.recommendations);
        renderXAI(data.details);
    } catch (err) {
        console.error(err);
        recResultsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <p>Failed to generate recommendations from backend.</p>
            </div>
        `;
    }
}

// Render recommendations
function renderRecommendations(recs) {
    recResultsList.innerHTML = '';
    
    if (recs.length === 0) {
        recResultsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💡</div>
                <p>No recommendation outputs available for this combination.</p>
            </div>
        `;
        return;
    }
    
    recs.forEach((rec, idx) => {
        const item = rec.item;
        const row = document.createElement('div');
        row.className = `rec-row-card ${idx === 0 ? 'highlight' : ''}`;
        
        const scoreLabel = activeAlgorithm === 'content' ? 'Similarity' : 'Predicted';
        // Content scores are 0-1 similarity, collaborative are predicted rating stars 1-5
        const scoreDisplay = activeAlgorithm === 'content' ? 
            `${(rec.score * 100).toFixed(0)}%` : 
            `${rec.score.toFixed(1)} ★`;
            
        const metaIcon = item.type === 'Movie' ? '🎬' : '📚';
        
        row.innerHTML = `
            <div class="rec-item-info">
                <div class="rec-title-row">
                    <span style="font-size: 16px;">${metaIcon}</span>
                    <span class="rec-item-title" title="${item.title}">${item.title}</span>
                </div>
                <span class="rec-item-meta">${item.author_director} • ${item.year}</span>
                <div class="rec-item-reason">
                    <span class="reason-bullet"></span>
                    <span>${rec.reason}</span>
                </div>
            </div>
            <div class="rec-score-wrapper">
                <span class="rec-score-value">${scoreDisplay}</span>
                <span class="rec-score-label">${scoreLabel}</span>
            </div>
        `;
        
        recResultsList.appendChild(row);
    });
}

// Render Explainable AI (XAI) calculations details
function renderXAI(details) {
    xaiSummary.innerHTML = details.summary;
    xaiVisualization.innerHTML = '';
    xaiConsoleLogs.innerHTML = '';
    
    // 1. Populate Visualization Section
    if (activeAlgorithm === 'content' && details.top_keywords) {
        const cloud = document.createElement('div');
        cloud.className = 'xai-cloud';
        
        details.top_keywords.forEach(kw => {
            const tag = document.createElement('span');
            tag.className = 'xai-keyword-tag';
            tag.innerHTML = `
                <span class="xai-keyword-name">${kw.word}</span>
                <span class="xai-keyword-score">${kw.weight.toFixed(2)}</span>
            `;
            cloud.appendChild(tag);
        });
        
        if (details.top_keywords.length === 0) {
            cloud.innerHTML = '<p class="text-muted" style="font-size:12px;">Add more ratings to create keywords profile.</p>';
        }
        xaiVisualization.appendChild(cloud);
        
    } else if (activeAlgorithm === 'collaborative' && details.similarities) {
        // User similarities
        details.similarities.forEach((sim, idx) => {
            const barRow = document.createElement('div');
            barRow.className = 'sim-bar-row';
            
            // Format percentage width
            const pct = Math.max(0, sim.score * 100);
            const fillType = idx === 0 ? 'fill-indigo' : 'fill-cyan';
            
            barRow.innerHTML = `
                <div class="sim-bar-label">
                    <span>${sim.user}</span>
                    <span style="font-weight:600; color: ${sim.score > 0 ? '#10b981' : '#ef4444'}">
                        ${sim.score > 0 ? '+' : ''}${sim.score.toFixed(2)}
                    </span>
                </div>
                <div class="sim-bar-container">
                    <div class="sim-bar-fill ${fillType}" style="width: ${pct}%"></div>
                </div>
            `;
            xaiVisualization.appendChild(barRow);
        });
    }
    
    // 2. Populate Console Mathematical Logs
    if (details.math_steps) {
        details.math_steps.forEach((step, idx) => {
            // Delay rendering slightly for cyber log effect
            const line = document.createElement('p');
            line.className = 'console-line';
            if (step.startsWith('-') || step.startsWith('Rated') || step.startsWith('Pearson') || step.startsWith('Comparison')) {
                line.className += ' indent';
            }
            line.textContent = `> ${step}`;
            xaiConsoleLogs.appendChild(line);
        });
        
        // Auto scroll console to top/bottom
        xaiConsoleLogs.scrollTop = 0;
    }
}

// Handle Custom Item Add Submit
async function handleAddItemSubmit(e) {
    e.preventDefault();
    
    const title = document.getElementById('itemTitle').value.trim();
    const author_director = document.getElementById('itemAuthorDirector').value.trim();
    const type = document.getElementById('itemType').value;
    const year = document.getElementById('itemYear').value;
    const genres = document.getElementById('itemGenres').value.trim();
    const description = document.getElementById('itemDescription').value.trim();
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Processing...</span>';
    
    try {
        const response = await fetch('/api/add_item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, author_director, type, year, genres, description })
        });
        
        if (!response.ok) throw new Error("Could not add custom item");
        
        const resData = await response.json();
        
        // Reset form
        addItemForm.reset();
        
        // Alert user of success (visual temporary notification)
        submitBtn.innerHTML = '<span>✓ Success! Fit Complete</span>';
        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>⚡ Add & Fit Model</span>';
        }, 2000);
        
        // Re-fetch catalog to update lists
        await fetchCatalog();
        
    } catch (err) {
        console.error(err);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>❌ Try Again</span>';
    }
}
