/**
 * Main demo application
 */

import { MatcherOrchestrator } from '../src/core/MatcherOrchestrator.js';
import { getConfig, saveConfig, resetConfig } from '../src/core/config.js';
import { exampleNotes, exampleSnippets, exampleRules } from '../src/data/testData.js';

class DemoApp {
  constructor() {
    this.config = getConfig();

    // Add example rules to config
    this.config.matchers.rules.rules = exampleRules;

    this.orchestrator = new MatcherOrchestrator(this.config);
    this.currentSnippet = null;
    this.currentMatches = null;
    this.notes = exampleNotes;

    this.init();
  }

  init() {
    this.renderExampleSnippets();
    this.renderAllNotes();
    this.renderMatcherStatus();
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Match button
    document.getElementById('match-btn').addEventListener('click', () => {
      const customText = document.getElementById('custom-snippet').value;
      if (customText.trim()) {
        this.matchSnippet({
          id: 'custom',
          text: customText,
          source: 'manual',
          timestamp: new Date()
        });
      }
    });

    // Settings button
    document.getElementById('settings-btn').addEventListener('click', () => {
      document.getElementById('settings-modal').classList.remove('hidden');
      this.renderSettings();
    });

    // Close settings modal
    document.querySelector('.modal-close').addEventListener('click', () => {
      document.getElementById('settings-modal').classList.add('hidden');
    });

    // Click outside modal to close
    document.getElementById('settings-modal').addEventListener('click', (e) => {
      if (e.target.id === 'settings-modal') {
        document.getElementById('settings-modal').classList.add('hidden');
      }
    });

    // Toggle matchers button
    document.getElementById('toggle-matchers').addEventListener('click', () => {
      document.getElementById('settings-modal').classList.remove('hidden');
      this.renderSettings();
    });

    // Reset config button
    document.getElementById('reset-config').addEventListener('click', () => {
      this.config = resetConfig();
      this.orchestrator = new MatcherOrchestrator(this.config);
      this.renderMatcherStatus();
      this.renderSettings();
      alert('Configuration reset to defaults!');
    });
  }

  renderExampleSnippets() {
    const container = document.getElementById('example-snippets');
    container.innerHTML = '';

    for (const snippet of exampleSnippets) {
      const item = document.createElement('div');
      item.className = 'snippet-item';
      item.innerHTML = `
        <div class="snippet-item-title">${snippet.metadata?.description || 'Example snippet'}</div>
        <div class="snippet-item-preview">${this.truncate(snippet.text, 60)}</div>
      `;
      item.addEventListener('click', () => this.selectSnippet(snippet, item));
      container.appendChild(item);
    }
  }

  selectSnippet(snippet, itemElement) {
    // Update UI
    document.querySelectorAll('.snippet-item').forEach(el => el.classList.remove('active'));
    itemElement.classList.add('active');

    // Display snippet
    const display = document.getElementById('current-snippet');
    display.innerHTML = `<pre>${snippet.text}</pre>`;

    // Display metadata
    const metadata = document.getElementById('snippet-metadata');
    metadata.innerHTML = '';

    if (snippet.metadata) {
      if (snippet.metadata.url) {
        metadata.innerHTML += `<span class="metadata-badge">🔗 ${snippet.metadata.url}</span>`;
      }
      if (snippet.source) {
        metadata.innerHTML += `<span class="metadata-badge">📍 ${snippet.source}</span>`;
      }
    }

    // Run matching
    this.matchSnippet(snippet);
  }

  async matchSnippet(snippet) {
    this.currentSnippet = snippet;

    // Show loading state
    document.getElementById('score-breakdown').innerHTML = '<p class="placeholder">Matching...</p>';
    document.getElementById('top-candidates').innerHTML = '<p class="placeholder">Calculating...</p>';

    // Run matching
    const result = await this.orchestrator.matchSnippet(snippet, this.notes);
    this.currentMatches = result;

    // Update UI
    this.renderMatcherStatus(result.matcherResults);
    this.renderScoreBreakdown(result.matches);
    this.renderTopCandidates(result.topMatches);

    if (result.topMatches.length > 0) {
      this.selectMatch(result.topMatches[0]);
    }
  }

  renderMatcherStatus(matcherResults = null) {
    const container = document.getElementById('matcher-status');
    container.innerHTML = '';

    const status = this.orchestrator.getMatchersStatus();

    for (const [name, info] of Object.entries(status)) {
      if (name === 'hybrid') continue; // Skip hybrid in this list

      const item = document.createElement('div');
      item.className = `matcher-item ${!info.enabled ? 'disabled' : ''}`;

      let score = 0;
      let scoreDisplay = '—';

      if (matcherResults && matcherResults.has(name)) {
        const matches = matcherResults.get(name);
        if (matches.length > 0) {
          score = matches[0].score;
          scoreDisplay = `${Math.round(score * 100)}%`;
        }
      }

      const colorClass = name === 'keyword' ? 'keyword' :
                         name === 'semantic' ? 'semantic' :
                         name === 'rules' ? 'rules' :
                         name === 'ner' ? 'ner' : 'contentType';

      item.innerHTML = `
        <div class="matcher-info">
          <span class="matcher-toggle">${info.enabled ? '☑' : '☐'}</span>
          <span class="matcher-name">${this.formatMatcherName(name)}</span>
        </div>
        <div class="matcher-score">
          <div class="progress-bar">
            <div class="progress-fill score-bar-fill ${colorClass}" style="width: ${score * 100}%"></div>
          </div>
          <span class="score-value">${scoreDisplay}</span>
        </div>
      `;

      item.querySelector('.matcher-toggle').addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleMatcher(name);
      });

      container.appendChild(item);
    }
  }

  renderScoreBreakdown(matches) {
    const container = document.getElementById('score-breakdown');

    if (!matches || matches.length === 0) {
      container.innerHTML = '<p class="placeholder">No matches found</p>';
      return;
    }

    const topMatch = matches[0];

    if (topMatch.breakdown) {
      container.innerHTML = '<div class="score-chart"></div>';
      const chart = container.querySelector('.score-chart');

      for (const [matcher, data] of Object.entries(topMatch.breakdown)) {
        const percentage = Math.round(data.score * 100);
        const colorClass = matcher === 'keyword' ? 'keyword' :
                           matcher === 'semantic' ? 'semantic' :
                           matcher === 'rules' ? 'rules' :
                           matcher === 'ner' ? 'ner' : 'contentType';

        chart.innerHTML += `
          <div class="score-bar">
            <div class="score-label">
              <span>${this.formatMatcherName(matcher)}</span>
              <span>${percentage}%</span>
            </div>
            <div class="score-bar-bg">
              <div class="score-bar-fill ${colorClass}" style="width: ${percentage}%">
                ${percentage > 10 ? percentage + '%' : ''}
              </div>
            </div>
          </div>
        `;
      }
    } else {
      // Single matcher result
      const percentage = Math.round(topMatch.score * 100);
      container.innerHTML = `
        <div class="score-chart">
          <div class="score-bar">
            <div class="score-label">
              <span>${this.formatMatcherName(topMatch.matcher)}</span>
              <span>${percentage}%</span>
            </div>
            <div class="score-bar-bg">
              <div class="score-bar-fill" style="width: ${percentage}%">
                ${percentage}%
              </div>
            </div>
          </div>
        </div>
      `;
    }
  }

  renderTopCandidates(candidates) {
    const container = document.getElementById('top-candidates');

    if (!candidates || candidates.length === 0) {
      container.innerHTML = '<p class="placeholder">No matches found</p>';
      return;
    }

    container.innerHTML = '';

    for (const match of candidates) {
      const note = this.notes.find(n => n.id === match.noteId);
      if (!note) continue;

      const item = document.createElement('div');
      item.className = 'candidate-item';
      item.innerHTML = `
        <div class="candidate-header">
          <span class="candidate-title">${note.title}</span>
          <span class="candidate-score">${Math.round(match.score * 100)}%</span>
        </div>
        <div class="candidate-reasoning">${match.reasoning || 'No reasoning provided'}</div>
      `;

      item.addEventListener('click', () => {
        document.querySelectorAll('.candidate-item').forEach(el => el.classList.remove('selected'));
        item.classList.add('selected');
        this.selectMatch(match);
      });

      container.appendChild(item);
    }

    // Select first by default
    container.firstChild?.classList.add('selected');
  }

  selectMatch(match) {
    const note = this.notes.find(n => n.id === match.noteId);
    if (!note) return;

    // Render best match
    const container = document.getElementById('best-match');
    container.innerHTML = `
      <div class="note-title">${note.title}</div>
      <div class="note-content">${note.content}</div>
      <div class="note-tags">
        ${note.tags?.map(tag => `<span class="tag">#${tag}</span>`).join('') || ''}
      </div>
    `;

    // Render insertion preview
    this.renderInsertionPreview(note);
  }

  renderInsertionPreview(note) {
    const container = document.getElementById('insertion-preview');

    if (!this.currentSnippet) {
      container.innerHTML = '<p class="placeholder">No snippet selected</p>';
      return;
    }

    // Show how the snippet would be added
    const lines = note.content.split('\n');
    const preview = [
      ...lines.slice(0, 3).map(line => `<div class="preview-line context">${this.escapeHtml(line)}</div>`),
      '<div class="preview-line added">...</div>',
      `<div class="preview-line added">+ ${this.escapeHtml(this.currentSnippet.text)} (${new Date().toLocaleDateString()})</div>`,
      '<div class="preview-line added">...</div>',
      ...lines.slice(-2).map(line => `<div class="preview-line context">${this.escapeHtml(line)}</div>`)
    ].join('');

    container.innerHTML = preview;
  }

  renderAllNotes() {
    const container = document.getElementById('all-notes');
    container.innerHTML = '';

    for (const note of this.notes) {
      const item = document.createElement('div');
      item.className = 'note-item';
      item.innerHTML = `
        <div class="note-item-title">${note.title}</div>
        <div class="note-item-preview">${this.truncate(note.content, 60)}</div>
      `;
      item.addEventListener('click', () => {
        this.showNoteDetails(note);
      });
      container.appendChild(item);
    }
  }

  showNoteDetails(note) {
    const container = document.getElementById('best-match');
    container.innerHTML = `
      <div class="note-title">${note.title}</div>
      <div class="note-content">${note.content}</div>
      <div class="note-tags">
        ${note.tags?.map(tag => `<span class="tag">#${tag}</span>`).join('') || ''}
      </div>
    `;
  }

  renderSettings() {
    this.renderMatcherToggles();
    this.renderWeightSliders();
    this.renderConfidenceSlider();
  }

  renderMatcherToggles() {
    const container = document.getElementById('matcher-toggles');
    container.innerHTML = '';

    const status = this.orchestrator.getMatchersStatus();

    for (const [name, info] of Object.entries(status)) {
      if (name === 'hybrid') continue;

      const label = document.createElement('label');
      label.innerHTML = `
        <input type="checkbox" ${info.enabled ? 'checked' : ''} data-matcher="${name}">
        ${this.formatMatcherName(name)}
      `;

      label.querySelector('input').addEventListener('change', (e) => {
        this.toggleMatcher(name);
      });

      container.appendChild(label);
    }
  }

  renderWeightSliders() {
    const container = document.getElementById('weight-sliders');
    container.innerHTML = '';

    const weights = this.orchestrator.hybridScorer.getWeights();

    for (const [matcher, weight] of Object.entries(weights)) {
      const label = document.createElement('label');
      label.innerHTML = `
        ${this.formatMatcherName(matcher)}: <span id="weight-${matcher}">${weight.toFixed(1)}</span>
        <input type="range" min="0" max="5" step="0.1" value="${weight}" data-matcher="${matcher}">
      `;

      label.querySelector('input').addEventListener('input', (e) => {
        const newWeight = parseFloat(e.target.value);
        document.getElementById(`weight-${matcher}`).textContent = newWeight.toFixed(1);
        this.orchestrator.hybridScorer.updateWeights({ [matcher]: newWeight });
        this.config.matchers.hybrid.weights[matcher] = newWeight;
        saveConfig(this.config);
      });

      container.appendChild(label);
    }
  }

  renderConfidenceSlider() {
    const slider = document.getElementById('confidence-threshold');
    const value = document.getElementById('confidence-value');

    slider.value = this.config.matchers.interactive.confidenceThreshold;
    value.textContent = this.config.matchers.interactive.confidenceThreshold;

    slider.addEventListener('input', (e) => {
      const newValue = parseFloat(e.target.value);
      value.textContent = newValue;
      this.config.matchers.interactive.confidenceThreshold = newValue;
      this.orchestrator.interactiveConfig.confidenceThreshold = newValue;
      saveConfig(this.config);
    });
  }

  toggleMatcher(name) {
    this.orchestrator.toggleMatcher(name, !this.orchestrator.matchers[name].enabled);
    this.config.matchers[name].enabled = this.orchestrator.matchers[name].enabled;
    saveConfig(this.config);
    this.renderMatcherStatus(this.currentMatches?.matcherResults);
    this.renderSettings();

    // Re-run matching if we have a current snippet
    if (this.currentSnippet) {
      this.matchSnippet(this.currentSnippet);
    }
  }

  formatMatcherName(name) {
    const names = {
      keyword: 'Keyword Matching',
      semantic: 'Semantic Similarity',
      rules: 'Rule-Based',
      ner: 'Named Entities (NER)',
      contentType: 'Content-Type Specific',
      hybrid: 'Hybrid Scorer'
    };
    return names[name] || name;
  }

  truncate(text, length) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new DemoApp());
} else {
  new DemoApp();
}
