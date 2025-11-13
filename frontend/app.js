// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let snippets = [];
let notes = [];
let currentSnippet = null;
let currentMatches = null;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    renderSnippets();
    loadHistory();

    // Set default timestamp for custom input
    document.getElementById('custom-timestamp').value = new Date().toISOString().slice(0, 16);
});

// Load data from API
async function loadData() {
    try {
        const [snippetsRes, notesRes] = await Promise.all([
            fetch(`${API_BASE_URL}/snippets`),
            fetch(`${API_BASE_URL}/notes`)
        ]);

        snippets = await snippetsRes.json();
        notes = await notesRes.json();
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load data. Make sure the backend server is running.');
    }
}

// Render snippets list
function renderSnippets() {
    const container = document.getElementById('snippets-list');
    container.innerHTML = '';

    snippets.forEach(snippet => {
        const item = document.createElement('div');
        item.className = 'snippet-item';
        item.onclick = () => selectSnippet(snippet);

        const content = document.createElement('div');
        content.className = 'snippet-content';
        content.textContent = snippet.content.length > 100
            ? snippet.content.substring(0, 100) + '...'
            : snippet.content;

        const meta = document.createElement('div');
        meta.className = 'snippet-meta';

        const sourceBadge = document.createElement('span');
        sourceBadge.className = `snippet-badge badge-${snippet.source}`;
        sourceBadge.textContent = snippet.source;

        const timestamp = document.createElement('span');
        timestamp.textContent = new Date(snippet.timestamp).toLocaleString();

        meta.appendChild(sourceBadge);
        meta.appendChild(timestamp);

        item.appendChild(content);
        item.appendChild(meta);
        container.appendChild(item);
    });
}

// Select a snippet and trigger matching
async function selectSnippet(snippet) {
    // Update UI
    document.querySelectorAll('.snippet-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.target.closest('.snippet-item').classList.add('selected');

    currentSnippet = snippet;
    await performMatch(snippet);
}

// Match custom snippet
async function matchCustomSnippet() {
    const content = document.getElementById('custom-snippet').value.trim();
    const timestamp = document.getElementById('custom-timestamp').value;

    if (!content) {
        alert('Please enter snippet content');
        return;
    }

    const customSnippet = {
        content: content,
        source: 'manual',
        timestamp: new Date(timestamp).toISOString(),
        metadata: {}
    };

    currentSnippet = customSnippet;
    await performMatch(customSnippet);
}

// Perform matching
async function performMatch(snippet) {
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/match`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ snippet })
        });

        const result = await response.json();
        currentMatches = result;

        renderMatches(result);

        // Check if manual review is needed
        if (result.requires_manual_review) {
            showManualReview(result);
        } else if (result.recommendation) {
            renderPreview(result.recommendation);
        }
    } catch (error) {
        console.error('Error matching snippet:', error);
        showError('Failed to match snippet');
    } finally {
        showLoading(false);
    }
}

// Render matching analysis
function renderMatches(result) {
    const container = document.getElementById('matching-analysis');
    container.innerHTML = '';

    // Show snippet being matched
    const snippetDisplay = document.createElement('div');
    snippetDisplay.className = 'snippet-display';
    snippetDisplay.innerHTML = `
        <strong>Input:</strong><br>
        ${escapeHtml(currentSnippet.content)}
    `;
    container.appendChild(snippetDisplay);

    // Show analysis header
    const header = document.createElement('h3');
    header.textContent = 'Matcher Results:';
    header.style.marginTop = '20px';
    header.style.marginBottom = '12px';
    container.appendChild(header);

    // Show matches
    const matchesList = document.createElement('div');
    matchesList.className = 'matches-list';

    if (result.matches.length === 0) {
        matchesList.innerHTML = '<div class="placeholder">No matches found</div>';
    } else {
        result.matches.slice(0, 5).forEach((match, index) => {
            const matchItem = renderMatchItem(match, index === 0);
            matchesList.appendChild(matchItem);
        });
    }

    container.appendChild(matchesList);
}

// Render a single match item
function renderMatchItem(match, isTop) {
    const item = document.createElement('div');
    item.className = `match-item ${isTop ? 'top-match' : ''}`;

    // Header with title and score
    const header = document.createElement('div');
    header.className = 'match-header';

    const titleDiv = document.createElement('div');
    const title = document.createElement('span');
    title.className = 'match-title';
    title.textContent = match.note_title;

    const confidenceBadge = document.createElement('span');
    confidenceBadge.className = `confidence-badge confidence-${match.confidence}`;
    confidenceBadge.textContent = match.confidence.toUpperCase();

    titleDiv.appendChild(title);
    titleDiv.appendChild(confidenceBadge);

    const score = document.createElement('div');
    score.className = 'match-score';
    score.textContent = (match.final_score * 100).toFixed(0) + '%';

    header.appendChild(titleDiv);
    header.appendChild(score);
    item.appendChild(header);

    // Matcher scores
    const scoresDiv = document.createElement('div');
    scoresDiv.className = 'matcher-scores';

    Object.entries(match.matcher_scores).forEach(([matcher, score]) => {
        const matcherDiv = document.createElement('div');
        matcherDiv.className = 'matcher-score';

        const name = document.createElement('div');
        name.className = 'matcher-name';
        name.textContent = matcher.charAt(0).toUpperCase() + matcher.slice(1) + 'Matcher';

        const barContainer = document.createElement('div');
        barContainer.className = 'score-bar-container';

        const bar = document.createElement('div');
        bar.className = 'score-bar';
        bar.style.width = (score * 100) + '%';

        const value = document.createElement('span');
        value.className = 'score-value';
        value.textContent = (score * 100).toFixed(0) + '%';

        if (score > 0) {
            bar.appendChild(value);
        }

        barContainer.appendChild(bar);
        matcherDiv.appendChild(name);
        matcherDiv.appendChild(barContainer);
        scoresDiv.appendChild(matcherDiv);
    });

    item.appendChild(scoresDiv);

    // Reasoning
    const reasoning = document.createElement('div');
    reasoning.className = 'match-reasoning';
    reasoning.textContent = match.reasoning;
    item.appendChild(reasoning);

    // Actions
    const actions = document.createElement('div');
    actions.className = 'match-actions';

    const applyBtn = document.createElement('button');
    applyBtn.className = 'btn-primary btn-apply';
    applyBtn.textContent = 'Apply This Match';
    applyBtn.onclick = () => applyMatch(match);

    const previewBtn = document.createElement('button');
    previewBtn.className = 'btn-secondary';
    previewBtn.textContent = 'Preview';
    previewBtn.onclick = () => renderPreview(match);

    actions.appendChild(previewBtn);
    actions.appendChild(applyBtn);
    item.appendChild(actions);

    return item;
}

// Render preview
function renderPreview(match) {
    const container = document.getElementById('preview-area');
    container.innerHTML = '';

    const preview = document.createElement('div');
    preview.className = 'note-preview';

    const title = document.createElement('div');
    title.className = 'note-title';
    title.textContent = match.note_title;

    const content = document.createElement('div');
    content.className = 'note-content';

    // Find the note
    const note = notes.find(n => n.id === match.note_id);
    if (note) {
        // Show note content with highlighted new addition
        const noteLines = note.content.split('\n');
        const previewText = match.preview;

        // For demo, append the preview at the end with highlight
        const contentHtml = escapeHtml(note.content) +
            '\n<span class="highlight-new">+ ' + escapeHtml(previewText) + '</span>';

        content.innerHTML = contentHtml;
    } else {
        content.textContent = 'Note not found';
    }

    preview.appendChild(title);
    preview.appendChild(content);
    container.appendChild(preview);
}

// Apply match
async function applyMatch(match, wasManualReview = false) {
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                snippet: currentSnippet,
                match: match,
                was_manual_review: wasManualReview
            })
        });

        const logEntry = await response.json();

        // Refresh history
        await loadHistory();

        // Show success message
        showSuccess(`Snippet sorted to "${match.note_title}"`);

        // Keep preview visible
        renderPreview(match);
    } catch (error) {
        console.error('Error applying match:', error);
        showError('Failed to apply match');
    } finally {
        showLoading(false);
    }
}

// Show manual review modal
function showManualReview(result) {
    const modal = document.getElementById('manual-review-modal');
    const message = document.getElementById('manual-review-message');
    const optionsContainer = document.getElementById('manual-review-options');

    message.textContent = result.reasoning;
    optionsContainer.innerHTML = '';

    // Show top matches as options
    result.matches.slice(0, 3).forEach(match => {
        const option = renderMatchItem(match, false);

        // Modify the apply button to close modal and mark as manual review
        const applyBtn = option.querySelector('.btn-apply');
        applyBtn.onclick = () => {
            closeManualReview();
            applyMatch(match, true);
        };

        optionsContainer.appendChild(option);
    });

    modal.classList.add('active');
}

// Close manual review modal
function closeManualReview() {
    document.getElementById('manual-review-modal').classList.remove('active');
}

// Load history
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history`);
        const history = await response.json();
        renderHistory(history);
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Render history
function renderHistory(history) {
    const container = document.getElementById('history-list');

    if (history.length === 0) {
        container.innerHTML = '<div class="placeholder">No actions yet</div>';
        return;
    }

    container.innerHTML = '';

    history.forEach(entry => {
        const item = document.createElement('div');
        item.className = 'history-item';

        const summary = document.createElement('div');
        summary.className = 'history-summary';
        summary.textContent = entry.get_summary || formatHistorySummary(entry);

        if (entry.was_manual_review) {
            const badge = document.createElement('span');
            badge.className = 'manual-review-badge';
            badge.textContent = 'MANUAL';
            summary.appendChild(badge);
        }

        const time = document.createElement('div');
        time.className = 'history-time';
        time.textContent = new Date(entry.timestamp).toLocaleString();

        item.appendChild(summary);
        item.appendChild(time);
        container.appendChild(item);
    });
}

// Format history summary (fallback if server doesn't provide get_summary)
function formatHistorySummary(entry) {
    const actionEmoji = {
        'append': '➕',
        'merge': '🔀',
        'link': '🔗',
        'create': '📝'
    };

    const emoji = actionEmoji[entry.action] || '📄';
    const content = entry.snippet_content.substring(0, 40);
    const truncated = entry.snippet_content.length > 40 ? '...' : '';

    return `${emoji} ${content}${truncated} → ${entry.matched_note_title}`;
}

// Utility functions
function showLoading(show) {
    document.getElementById('loading-spinner').style.display = show ? 'flex' : 'none';
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    // Simple success notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: #50c878;
        color: white;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = '✓ ' + message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add animations to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
