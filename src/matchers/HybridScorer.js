/**
 * Hybrid Weighted Scoring System
 * Combines results from multiple matchers with configurable weights
 */

import { MatcherTypes } from '../core/types.js';

export class HybridScorer {
  constructor(config) {
    this.config = config;
    this.enabled = config.enabled !== false;
    this.weights = config.weights || {};
  }

  /**
   * Combine match results from multiple matchers
   * @param {Map<string, import('../core/types.js').Match[]>} matcherResults
   * @returns {Promise<import('../core/types.js').Match[]>}
   */
  async combineMatches(matcherResults) {
    if (!this.enabled || matcherResults.size === 0) {
      return [];
    }

    // Group matches by noteId
    const noteMatches = new Map();

    for (const [matcher, matches] of matcherResults) {
      for (const match of matches) {
        if (!noteMatches.has(match.noteId)) {
          noteMatches.set(match.noteId, []);
        }
        noteMatches.get(match.noteId).push({
          ...match,
          matcher
        });
      }
    }

    // Calculate combined scores
    const combinedMatches = [];

    for (const [noteId, matches] of noteMatches) {
      const finalScore = this.calculateCombinedScore(matches);
      const breakdown = this.calculateBreakdown(matches);

      // Collect all matched terms and reasoning
      const allMatchedTerms = new Set();
      const allReasoning = [];

      for (const match of matches) {
        if (match.matchedTerms) {
          match.matchedTerms.forEach(term => allMatchedTerms.add(term));
        }
        if (match.reasoning) {
          allReasoning.push(`[${match.matcher}] ${match.reasoning}`);
        }
      }

      combinedMatches.push({
        noteId,
        score: finalScore,
        matcher: MatcherTypes.HYBRID,
        reasoning: `Combined from ${matches.length} matchers:\n${allReasoning.join('\n')}`,
        matchedTerms: Array.from(allMatchedTerms),
        breakdown
      });
    }

    return combinedMatches.sort((a, b) => b.score - a.score);
  }

  /**
   * Calculate combined score for a note
   * @private
   */
  calculateCombinedScore(matches) {
    const method = this.config.combineMethod || 'weighted-sum';

    switch (method) {
      case 'weighted-sum':
        return this.weightedSum(matches);
      case 'multiply':
        return this.multiply(matches);
      case 'max':
        return this.max(matches);
      default:
        return this.weightedSum(matches);
    }
  }

  /**
   * Weighted sum combination
   * @private
   */
  weightedSum(matches) {
    let weightedScore = 0;
    let totalWeight = 0;

    for (const match of matches) {
      const weight = this.weights[match.matcher] || 1.0;
      weightedScore += match.score * weight;
      totalWeight += weight;
    }

    return totalWeight > 0 ? weightedScore / totalWeight : 0;
  }

  /**
   * Multiply scores (geometric mean)
   * @private
   */
  multiply(matches) {
    if (matches.length === 0) return 0;

    let product = 1;
    for (const match of matches) {
      product *= match.score;
    }

    // Return geometric mean
    return Math.pow(product, 1 / matches.length);
  }

  /**
   * Take maximum score
   * @private
   */
  max(matches) {
    if (matches.length === 0) return 0;
    return Math.max(...matches.map(m => m.score));
  }

  /**
   * Calculate score breakdown for visualization
   * @param {import('../core/types.js').Match[]} matches
   * @returns {Object}
   */
  calculateBreakdown(matches) {
    const breakdown = {};

    for (const match of matches) {
      const weight = this.weights[match.matcher] || 1.0;
      const contribution = match.score * weight;

      breakdown[match.matcher] = {
        score: match.score,
        weight,
        contribution
      };
    }

    return breakdown;
  }

  /**
   * Normalize scores to [0, 1] range
   * @param {number[]} scores
   * @returns {number[]}
   */
  normalizeScores(scores) {
    const method = this.config.normalizationMethod || 'minmax';

    switch (method) {
      case 'minmax':
        return this.minMaxNormalize(scores);
      case 'zscore':
        return this.zScoreNormalize(scores);
      case 'softmax':
        return this.softmaxNormalize(scores);
      default:
        return scores;
    }
  }

  /**
   * Min-max normalization
   * @private
   */
  minMaxNormalize(scores) {
    const min = Math.min(...scores);
    const max = Math.max(...scores);
    const range = max - min;

    if (range === 0) return scores.map(() => 1);

    return scores.map(s => (s - min) / range);
  }

  /**
   * Z-score normalization
   * @private
   */
  zScoreNormalize(scores) {
    const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
    const variance = scores.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / scores.length;
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return scores.map(() => 0);

    return scores.map(s => (s - mean) / stdDev);
  }

  /**
   * Softmax normalization
   * @private
   */
  softmaxNormalize(scores) {
    const expScores = scores.map(s => Math.exp(s));
    const sumExp = expScores.reduce((a, b) => a + b, 0);

    return expScores.map(e => e / sumExp);
  }

  /**
   * Update weights configuration
   * @param {Object} newWeights
   */
  updateWeights(newWeights) {
    this.weights = { ...this.weights, ...newWeights };
  }

  /**
   * Get current weights
   * @returns {Object}
   */
  getWeights() {
    return { ...this.weights };
  }
}
