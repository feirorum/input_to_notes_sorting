/**
 * Rule-Based Category System
 * Allows users to define explicit matching rules
 */

import { MatcherTypes } from '../core/types.js';

export class RuleBasedMatcher {
  constructor(config) {
    this.config = config;
    this.enabled = config.enabled !== false;
    this.rules = config.rules || [];
  }

  /**
   * Match snippet against notes using user-defined rules
   * @param {import('../core/types.js').Snippet} snippet
   * @param {import('../core/types.js').Note[]} notes
   * @returns {Promise<import('../core/types.js').Match[]>}
   */
  async match(snippet, notes) {
    if (!this.enabled || !snippet.text || this.rules.length === 0) {
      return [];
    }

    const matches = [];
    const sortedRules = [...this.rules].sort((a, b) => (a.priority || 0) - (b.priority || 0));

    for (const rule of sortedRules) {
      if (this.evaluateRule(rule, snippet)) {
        matches.push({
          noteId: rule.noteId,
          score: 1.0, // Rules are binary: match or no match
          matcher: MatcherTypes.RULES,
          reasoning: `Matched rule: ${rule.name || rule.id}`,
          matchedTerms: [rule.name || rule.id]
        });

        // If matchMode is 'first', stop after first match
        if (this.config.matchMode === 'first') {
          break;
        }
      }
    }

    return matches;
  }

  /**
   * Evaluate a single rule against snippet
   * @param {Object} rule
   * @param {import('../core/types.js').Snippet} snippet
   * @returns {boolean}
   */
  evaluateRule(rule, snippet) {
    if (!rule.conditions) return false;

    return this.evaluateConditions(rule.conditions, snippet.text);
  }

  /**
   * Recursively evaluate conditions
   * @private
   */
  evaluateConditions(conditions, text) {
    const { type, rules } = conditions;

    if (!rules || rules.length === 0) return false;

    const results = rules.map(rule => {
      // If rule has nested conditions, recurse
      if (rule.type === 'AND' || rule.type === 'OR' || rule.type === 'NOT') {
        return this.evaluateConditions(rule, text);
      }

      // Otherwise, evaluate single condition
      return this.evaluateSingleCondition(rule, text);
    });

    switch (type) {
      case 'AND':
        return results.every(r => r);
      case 'OR':
        return results.some(r => r);
      case 'NOT':
        return !results[0];
      default:
        return false;
    }
  }

  /**
   * Evaluate a single condition
   * @private
   */
  evaluateSingleCondition(condition, text) {
    const { type, value, caseSensitive } = condition;
    const testText = caseSensitive ? text : text.toLowerCase();
    const testValue = caseSensitive ? value : value.toLowerCase();

    switch (type) {
      case 'keyword':
        return testText.includes(testValue);

      case 'regex':
        try {
          const flags = caseSensitive ? '' : 'i';
          const regex = new RegExp(testValue, flags);
          return regex.test(text);
        } catch (e) {
          console.error('Invalid regex:', testValue, e);
          return false;
        }

      case 'contains':
        return testText.includes(testValue);

      case 'startsWith':
        return testText.startsWith(testValue);

      case 'endsWith':
        return testText.endsWith(testValue);

      case 'equals':
        return testText === testValue;

      default:
        return false;
    }
  }

  /**
   * Validate a rule structure
   * @param {Object} rule
   * @returns {boolean}
   */
  validateRule(rule) {
    if (!rule.id || !rule.noteId) return false;
    if (!rule.conditions) return false;

    return this.validateConditions(rule.conditions);
  }

  /**
   * Validate conditions structure
   * @private
   */
  validateConditions(conditions) {
    if (!conditions.type) return false;
    if (!['AND', 'OR', 'NOT'].includes(conditions.type)) return false;
    if (!Array.isArray(conditions.rules)) return false;

    return conditions.rules.every(rule => {
      if (rule.type === 'AND' || rule.type === 'OR' || rule.type === 'NOT') {
        return this.validateConditions(rule);
      }
      return rule.type && rule.value !== undefined;
    });
  }

  /**
   * Test a rule against sample text
   * @param {Object} rule
   * @param {string} testText
   * @returns {boolean}
   */
  testRule(rule, testText) {
    return this.evaluateRule(rule, { text: testText });
  }

  /**
   * Add a new rule
   * @param {Object} rule
   */
  addRule(rule) {
    if (this.validateRule(rule)) {
      this.rules.push(rule);
      return true;
    }
    return false;
  }

  /**
   * Remove a rule by ID
   * @param {string} ruleId
   */
  removeRule(ruleId) {
    const index = this.rules.findIndex(r => r.id === ruleId);
    if (index !== -1) {
      this.rules.splice(index, 1);
      return true;
    }
    return false;
  }
}
