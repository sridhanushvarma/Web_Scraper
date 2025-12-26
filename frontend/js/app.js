/**
 * Web Scraper Frontend Application
 * Handles user interactions, API calls, and data visualization
 */

// API Configuration
const API_BASE = '';  // Same origin

// State
let currentData = [];
let currentView = 'table';

// DOM Elements
const elements = {
    urlInput: document.getElementById('url-input'),
    scraperType: document.getElementById('scraper-type'),
    categorySelect: document.getElementById('category-select'),
    presetSelect: document.getElementById('preset-select'),
    suggestPresetsBtn: document.getElementById('suggest-presets-btn'),
    containerSelector: document.getElementById('container-selector'),
    fieldsContainer: document.getElementById('fields-container'),
    addFieldBtn: document.getElementById('add-field-btn'),
    scrapeBtn: document.getElementById('scrape-btn'),
    detectBtn: document.getElementById('detect-btn'),
    detectResult: document.getElementById('detect-result'),
    waitSelector: document.getElementById('wait-selector'),
    timeout: document.getElementById('timeout'),
    enablePagination: document.getElementById('enable-pagination'),
    paginationOptions: document.getElementById('pagination-options'),
    nextPageSelector: document.getElementById('next-page-selector'),
    maxPages: document.getElementById('max-pages'),
    statusBar: document.getElementById('status-bar'),
    resultsContainer: document.getElementById('results-container'),
    emptyState: document.getElementById('empty-state'),
    loadingState: document.getElementById('loading-state'),
    tableView: document.getElementById('table-view'),
    cardsView: document.getElementById('cards-view'),
    jsonView: document.getElementById('json-view'),
    metadata: document.getElementById('metadata'),
    exportCsv: document.getElementById('export-csv'),
    exportJson: document.getElementById('export-json'),
    viewBtns: document.querySelectorAll('.view-btn')
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadPresets();
    addField();  // Add one empty field by default
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    elements.scrapeBtn.addEventListener('click', startScraping);
    elements.detectBtn.addEventListener('click', detectPageType);
    elements.addFieldBtn.addEventListener('click', () => addField());
    elements.categorySelect.addEventListener('change', () => loadPresets(elements.categorySelect.value));
    elements.presetSelect.addEventListener('change', loadPresetConfig);
    elements.suggestPresetsBtn.addEventListener('click', suggestPresetsForUrl);
    elements.enablePagination.addEventListener('change', togglePaginationOptions);
    elements.exportCsv.addEventListener('click', () => exportData('csv'));
    elements.exportJson.addEventListener('click', () => exportData('json'));
    
    elements.viewBtns.forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });
}

// Load available categories
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/api/categories`);
        const categories = await response.json();
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = `${category.name} - ${category.description}`;
            elements.categorySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Load available presets
async function loadPresets(category = null) {
    try {
        // Clear existing presets
        elements.presetSelect.innerHTML = '<option value="">-- Select a preset --</option>';
        
        const url = category 
            ? `${API_BASE}/api/categories/${category}/presets`
            : `${API_BASE}/api/presets`;
        
        const response = await fetch(url);
        const presets = await response.json();
        
        presets.forEach(preset => {
            const option = document.createElement('option');
            option.value = preset.id;
            const categoryLabel = preset.category ? ` [${preset.category}]` : '';
            option.textContent = `${preset.name}${categoryLabel} - ${preset.description}`;
            elements.presetSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load presets:', error);
    }
}

// Suggest presets based on URL
async function suggestPresetsForUrl() {
    const url = elements.urlInput.value.trim();
    if (!url) {
        showStatus('Please enter a URL first', 'warning');
        return;
    }

    try {
        elements.suggestPresetsBtn.disabled = true;
        elements.suggestPresetsBtn.innerHTML = `
            <svg class="w-4 h-4 mr-1 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Analyzing...
        `;

        const response = await fetch(`${API_BASE}/api/suggest-presets?url=${encodeURIComponent(url)}`);
        const result = await response.json();

        if (result.suggestions && result.suggestions.length > 0) {
            // Clear and populate presets
            elements.presetSelect.innerHTML = '<option value="">-- Select a preset --</option>';
            result.suggestions.forEach(preset => {
                const option = document.createElement('option');
                option.value = preset.id;
                option.textContent = `⭐ ${preset.name} - ${preset.description}`;
                elements.presetSelect.appendChild(option);
            });
            
            // Select first suggestion
            elements.presetSelect.value = result.suggestions[0].id;
            loadPresetConfig();
            
            showStatus(`Found ${result.suggestions.length} suggested preset(s)`, 'success');
        } else {
            showStatus('No presets suggested. Try selecting a category manually.', 'info');
        }
    } catch (error) {
        showStatus('Failed to get suggestions', 'error');
    } finally {
        elements.suggestPresetsBtn.disabled = false;
        elements.suggestPresetsBtn.innerHTML = `
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
            Suggest presets for URL
        `;
    }
}

// Load preset configuration
async function loadPresetConfig() {
    const presetId = elements.presetSelect.value;
    if (!presetId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/presets/${presetId}`);
        const config = await response.json();
        
        // Set container selector
        elements.containerSelector.value = config.container_selector || '';
        
        // Clear and add fields
        elements.fieldsContainer.innerHTML = '';
        config.fields.forEach(field => addField(field));
        
        showStatus(`Loaded preset: ${config.name}`, 'info');
    } catch (error) {
        showStatus('Failed to load preset configuration', 'error');
    }
}

// Add extraction field
function addField(fieldConfig = null) {
    const fieldId = Date.now();
    const fieldHtml = `
        <div class="field-card" data-field-id="${fieldId}">
            <div class="flex items-center justify-between mb-2">
                <input type="text" class="field-name flex-1 px-2 py-1 text-sm border rounded mr-2"
                       placeholder="Field name" value="${fieldConfig?.name || ''}">
                <button class="field-remove-btn" onclick="removeField(${fieldId})" title="Remove field">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="flex space-x-2 mb-2">
                <input type="text" class="field-selector flex-1 px-2 py-1 text-sm border rounded"
                       placeholder="CSS selector or XPath" value="${fieldConfig?.selector || ''}">
                <select class="field-type px-2 py-1 text-sm border rounded bg-white">
                    <option value="css" ${fieldConfig?.selector_type !== 'xpath' ? 'selected' : ''}>CSS</option>
                    <option value="xpath" ${fieldConfig?.selector_type === 'xpath' ? 'selected' : ''}>XPath</option>
                </select>
            </div>
            <div class="flex space-x-2 text-xs">
                <input type="text" class="field-attribute flex-1 px-2 py-1 border rounded"
                       placeholder="Attribute (e.g., href, src)" value="${fieldConfig?.attribute || ''}">
                <label class="flex items-center">
                    <input type="checkbox" class="field-multiple mr-1" ${fieldConfig?.multiple ? 'checked' : ''}>
                    Multiple
                </label>
            </div>
        </div>
    `;
    elements.fieldsContainer.insertAdjacentHTML('beforeend', fieldHtml);
}

// Remove field
function removeField(fieldId) {
    const field = document.querySelector(`[data-field-id="${fieldId}"]`);
    if (field && elements.fieldsContainer.children.length > 1) {
        field.remove();
    }
}

// Toggle pagination options
function togglePaginationOptions() {
    elements.paginationOptions.classList.toggle('hidden', !elements.enablePagination.checked);
}

// Detect page type
async function detectPageType() {
    const url = elements.urlInput.value.trim();
    if (!url) {
        showStatus('Please enter a URL', 'warning');
        return;
    }

    try {
        elements.detectBtn.disabled = true;
        elements.detectBtn.innerHTML = `
            <svg class="w-4 h-4 mr-1 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Detecting...
        `;

        const response = await fetch(`${API_BASE}/api/detect?url=${encodeURIComponent(url)}`);
        const result = await response.json();

        // Clean indicators (remove emojis)
        const cleanIndicators = result.indicators.map(i => i.replace(/[\u{1F300}-\u{1F9FF}]/gu, '').trim());

        elements.detectResult.classList.remove('hidden');
        elements.detectResult.innerHTML = `
            <strong>Recommendation:</strong> ${result.recommended_scraper}<br>
            <strong>Confidence:</strong> ${(result.confidence * 100).toFixed(0)}%<br>
            <strong>Indicators:</strong><br>
            <ul class="text-xs mt-1 pl-4 list-disc">
                ${cleanIndicators.map(i => `<li>${i}</li>`).join('')}
            </ul>
        `;

        // Auto-select recommended scraper
        elements.scraperType.value = result.recommended_scraper;
    } catch (error) {
        showStatus('Failed to detect page type', 'error');
    } finally {
        elements.detectBtn.disabled = false;
        elements.detectBtn.innerHTML = `
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            Auto-detect page type
        `;
    }
}

// Collect field configurations
function collectFields() {
    const fields = [];
    const fieldCards = elements.fieldsContainer.querySelectorAll('.field-card');

    fieldCards.forEach(card => {
        const name = card.querySelector('.field-name').value.trim();
        const selector = card.querySelector('.field-selector').value.trim();
        const selectorType = card.querySelector('.field-type').value;
        const attribute = card.querySelector('.field-attribute').value.trim();
        const multiple = card.querySelector('.field-multiple').checked;

        if (name && selector) {
            fields.push({
                name,
                selector,
                selector_type: selectorType,
                attribute: attribute || null,
                multiple
            });
        }
    });

    return fields;
}

// Start scraping
async function startScraping() {
    const url = elements.urlInput.value.trim();
    if (!url) {
        showStatus('Please enter a URL', 'warning');
        return;
    }

    const fields = collectFields();
    if (fields.length === 0) {
        showStatus('Please add at least one extraction field', 'warning');
        return;
    }

    // Build request
    const request = {
        url,
        scraper_type: elements.scraperType.value,
        fields,
        container_selector: elements.containerSelector.value.trim() || null,
        wait_for_selector: elements.waitSelector.value.trim() || null,
        timeout: parseInt(elements.timeout.value) || 30
    };

    // Add pagination if enabled
    if (elements.enablePagination.checked) {
        request.pagination = {
            enabled: true,
            next_page_selector: elements.nextPageSelector.value.trim() || null,
            max_pages: parseInt(elements.maxPages.value) || 5
        };
    }

    try {
        showLoading(true);
        elements.scrapeBtn.disabled = true;
        elements.scrapeBtn.innerHTML = `
            <svg class="w-5 h-5 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Scraping...
        `;

        const response = await fetch(`${API_BASE}/api/scrape`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });

        const result = await response.json();

        if (result.success) {
            currentData = result.result.data;
            showResults(result.result);
            showStatus(
                `Scraped ${result.result.total_items} items from ${result.result.pages_scraped} page(s) in ${result.result.elapsed_time}s`,
                'success'
            );
        } else {
            showStatus(`Error: ${result.error.message}`, 'error');
            showEmptyState();
        }
    } catch (error) {
        showStatus(`Network error: ${error.message}`, 'error');
        showEmptyState();
    } finally {
        showLoading(false);
        elements.scrapeBtn.disabled = false;
        elements.scrapeBtn.innerHTML = `
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            Start Scraping
        `;
    }
}

// Show results
function showResults(result) {
    elements.emptyState.classList.add('hidden');
    elements.exportCsv.classList.remove('hidden');
    elements.exportJson.classList.remove('hidden');

    // Show metadata
    elements.metadata.classList.remove('hidden');
    elements.metadata.innerHTML = `
        <div class="flex justify-between items-center">
            <span><strong>URL:</strong> <a href="${result.url}" target="_blank" class="text-blue-600 hover:underline">${result.url}</a></span>
            <span><strong>Scraper:</strong> ${result.scraper_used}</span>
            <span><strong>Items:</strong> ${result.total_items}</span>
            <span><strong>Pages:</strong> ${result.pages_scraped}</span>
            <span><strong>Time:</strong> ${result.elapsed_time}s</span>
        </div>
    `;

    // Render views
    renderTableView(result.data);
    renderCardsView(result.data);
    renderJsonView(result.data);

    // Show current view
    switchView(currentView);
}

// Render table view
function renderTableView(data) {
    if (data.length === 0) {
        elements.tableView.innerHTML = '<p class="text-gray-500 text-center py-4">No data found</p>';
        return;
    }

    const headers = Object.keys(data[0]).filter(k => !k.startsWith('_'));

    let html = '<table class="data-table"><thead><tr>';
    headers.forEach(h => { html += `<th>${h}</th>`; });
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        headers.forEach(h => {
            let value = row[h];
            if (Array.isArray(value)) value = value.join(', ');
            if (typeof value === 'string' && value.startsWith('http')) {
                value = `<a href="${value}" target="_blank" class="text-blue-600 hover:underline">Link</a>`;
            }
            html += `<td>${value ?? '-'}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    elements.tableView.innerHTML = html;
}

// Render cards view
function renderCardsView(data) {
    if (data.length === 0) {
        elements.cardsView.innerHTML = '<p class="text-gray-500 text-center py-4 col-span-2">No data found</p>';
        return;
    }

    const headers = Object.keys(data[0]).filter(k => !k.startsWith('_'));

    let html = '';
    data.forEach((row, idx) => {
        html += `<div class="data-card">`;
        html += `<div class="data-card-header">Item ${idx + 1}</div>`;
        headers.forEach(h => {
            let value = row[h];
            if (Array.isArray(value)) value = value.join(', ');
            if (typeof value === 'string' && value.startsWith('http')) {
                value = `<a href="${value}" target="_blank" class="text-blue-600 hover:underline">${value.substring(0, 50)}...</a>`;
            }
            html += `<div class="data-card-field"><span class="data-card-field-label">${h}:</span> <span class="data-card-field-value">${value ?? '-'}</span></div>`;
        });
        html += '</div>';
    });

    elements.cardsView.innerHTML = html;
}

// Render JSON view
function renderJsonView(data) {
    elements.jsonView.querySelector('pre').textContent = JSON.stringify(data, null, 2);
}

// Switch view
function switchView(view) {
    currentView = view;

    elements.viewBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    elements.tableView.classList.toggle('hidden', view !== 'table');
    elements.cardsView.classList.toggle('hidden', view !== 'cards');
    elements.jsonView.classList.toggle('hidden', view !== 'json');
}

// Show status message
function showStatus(message, type = 'info') {
    elements.statusBar.classList.remove('hidden', 'status-success', 'status-error', 'status-warning', 'status-info');
    elements.statusBar.classList.add(`status-${type}`);
    elements.statusBar.textContent = message;
}

// Show/hide loading state
function showLoading(show) {
    elements.loadingState.classList.toggle('hidden', !show);
    elements.emptyState.classList.add('hidden');
    elements.tableView.classList.add('hidden');
    elements.cardsView.classList.add('hidden');
    elements.jsonView.classList.add('hidden');
}

// Show empty state
function showEmptyState() {
    elements.emptyState.classList.remove('hidden');
    elements.tableView.classList.add('hidden');
    elements.cardsView.classList.add('hidden');
    elements.jsonView.classList.add('hidden');
    elements.metadata.classList.add('hidden');
    elements.exportCsv.classList.add('hidden');
    elements.exportJson.classList.add('hidden');
}

// Export data
function exportData(format) {
    if (currentData.length === 0) return;

    let content, filename, mimeType;

    if (format === 'json') {
        content = JSON.stringify(currentData, null, 2);
        filename = 'scraped_data.json';
        mimeType = 'application/json';
    } else if (format === 'csv') {
        const headers = Object.keys(currentData[0]).filter(k => !k.startsWith('_'));
        const rows = [headers.join(',')];
        currentData.forEach(row => {
            const values = headers.map(h => {
                let v = row[h];
                if (Array.isArray(v)) v = v.join('; ');
                if (typeof v === 'string' && (v.includes(',') || v.includes('"'))) {
                    v = `"${v.replace(/"/g, '""')}"`;
                }
                return v ?? '';
            });
            rows.push(values.join(','));
        });
        content = rows.join('\n');
        filename = 'scraped_data.csv';
        mimeType = 'text/csv';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Make removeField globally accessible
window.removeField = removeField;

