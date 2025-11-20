/**
 * Matcher Orchestrator
 * Coordinates all matchers and interactive disambiguation
 */

import { KeywordMatcher } from '../matchers/KeywordMatcher.js';
import { RuleBasedMatcher } from '../matchers/RuleBasedMatcher.js';
import { NERMatcher } from '../matchers/NERMatcher.js';
import { ContentTypeMatcher } from '../matchers/ContentTypeMatcher.js';
import { HybridScorer } from '../matchers/HybridScorer.js';

export class MatcherOrchestrator {
  constructor(config) {
    this.config = config;

    // Initialize all matchers
    this.matchers = {
      keyword: new KeywordMatcher(config.matchers.keyword),
      rules: new RuleBasedMatcher(config.matchers.rules),
      ner: new NERMatcher(config.matchers.ner),
      contentType: new ContentTypeMatcher(config.matchers.contentType)
    };

    // Initialize hybrid scorer
    this.hybridScorer = new HybridScorer(config.matchers.hybrid);

    // Interactive disambiguation config
    this.interactiveConfig = config.matchers.interactive;
  }

  /**
   * Match a snippet against notes using all enabled matchers
   * @param {import('./types.js').Snippet} snippet
   * @param {import('./types.js').Note[]} notes
   * @returns {Promise<Object>} - { matches, needsDisambiguation, suggestion }
   */
  async matchSnippet(snippet, notes) {
    // Run all enabled matchers in parallel
    const matcherResults = new Map();

    const promises = [];
    for (const [name, matcher] of Object.entries(this.matchers)) {
      if (matcher.enabled) {
        promises.push(
          matcher.match(snippet, notes).then(matches => {
            matcherResults.set(name, matches);
          })
        );
      }
    }

    await Promise.all(promises);

    // Combine results with hybrid scorer if enabled
    let finalMatches;
    if (this.hybridScorer.enabled && matcherResults.size > 0) {
      finalMatches = await this.hybridScorer.combineMatches(matcherResults);
    } else {
      // If hybrid scorer is disabled, just flatten all matches
      finalMatches = [];
      for (const matches of matcherResults.values()) {
        finalMatches.push(...matches);
      }
      finalMatches.sort((a, b) => b.score - a.score);
    }

    // Check if interactive disambiguation is needed
    const disambiguation = this.checkDisambiguation(finalMatches);

    return {
      matches: finalMatches,
      matcherResults, // Individual matcher results for visualization
      needsDisambiguation: disambiguation.needed,
      suggestion: disambiguation.suggestion,
      topMatches: finalMatches.slice(0, this.interactiveConfig.maxSuggestions)
    };
  }

  /**
   * Check if interactive disambiguation is needed
   * @private
   */
  checkDisambiguation(matches) {
    if (!this.interactiveConfig.enabled) {
      return {
        needed: false,
        suggestion: matches[0] || null
      };
    }

    if (matches.length === 0) {
      return {
        needed: true,
        suggestion: null
      };
    }

    if (matches.length === 1 && this.interactiveConfig.autoSortIfSingleMatch) {
      return {
        needed: false,
        suggestion: matches[0]
      };
    }

    // Calculate confidence
    const topScore = matches[0].score;
    const totalScore = matches.reduce((sum, m) => sum + m.score, 0);
    const confidence = totalScore > 0 ? topScore / totalScore : 0;

    if (confidence >= this.interactiveConfig.confidenceThreshold) {
      return {
        needed: false,
        suggestion: matches[0]
      };
    }

    return {
      needed: true,
      suggestion: matches[0]
    };
  }

  /**
   * Record user's choice for learning
   * @param {import('./types.js').Snippet} snippet
   * @param {string} selectedNoteId
   * @param {import('./types.js').Match[]} suggestedMatches
   */
  recordChoice(snippet, selectedNoteId, suggestedMatches) {
    if (!this.interactiveConfig.rememberChoices) {
      return;
    }

    // Store in localStorage for future learning
    try {
      const history = JSON.parse(localStorage.getItem('matchingHistory') || '[]');
      history.push({
        snippet: snippet.text,
        selectedNoteId,
        suggestedMatches: suggestedMatches.map(m => ({
          noteId: m.noteId,
          score: m.score,
          matcher: m.matcher
        })),
        timestamp: new Date().toISOString()
      });

      // Keep only last 100 entries
      if (history.length > 100) {
        history.shift();
      }

      localStorage.setItem('matchingHistory', JSON.stringify(history));
    } catch (e) {
      console.error('Failed to record choice:', e);
    }
  }

  /**
   * Get matching statistics
   * @returns {Object}
   */
  getStatistics() {
    try {
      const history = JSON.parse(localStorage.getItem('matchingHistory') || '[]');

      const stats = {
        totalMatches: history.length,
        matcherAccuracy: {},
        averageConfidence: 0
      };

      // Calculate matcher accuracy (how often top match was selected)
      for (const entry of history) {
        if (entry.suggestedMatches && entry.suggestedMatches.length > 0) {
          const topMatch = entry.suggestedMatches[0];
          const wasCorrect = topMatch.noteId === entry.selectedNoteId;

          if (!stats.matcherAccuracy[topMatch.matcher]) {
            stats.matcherAccuracy[topMatch.matcher] = {
              correct: 0,
              total: 0
            };
          }

          stats.matcherAccuracy[topMatch.matcher].total++;
          if (wasCorrect) {
            stats.matcherAccuracy[topMatch.matcher].correct++;
          }
        }
      }

      return stats;
    } catch (e) {
      console.error('Failed to get statistics:', e);
      return {
        totalMatches: 0,
        matcherAccuracy: {},
        averageConfidence: 0
      };
    }
  }

  /**
   * Update matcher configuration
   * @param {string} matcherName
   * @param {Object} config
   */
  updateMatcherConfig(matcherName, config) {
    if (this.matchers[matcherName]) {
      this.matchers[matcherName].config = {
        ...this.matchers[matcherName].config,
        ...config
      };
    }
  }

  /**
   * Toggle matcher enabled state
   * @param {string} matcherName
   * @param {boolean} enabled
   */
  toggleMatcher(matcherName, enabled) {
    if (this.matchers[matcherName]) {
      this.matchers[matcherName].enabled = enabled;
    }
  }

  /**
   * Get all matchers status
   * @returns {Object}
   */
  getMatchersStatus() {
    const status = {};
    for (const [name, matcher] of Object.entries(this.matchers)) {
      status[name] = {
        enabled: matcher.enabled,
        type: matcher.constructor.name
      };
    }
    status.hybrid = {
      enabled: this.hybridScorer.enabled,
      weights: this.hybridScorer.getWeights()
    };
    return status;
  }
}
