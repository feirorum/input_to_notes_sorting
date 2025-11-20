/**
 * Simple Keyword Matching using TF-IDF
 */

import { extractKeywords, extractNGrams, calculateTFIDF, normalize } from '../utils/text.js';
import { MatcherTypes } from '../core/types.js';

export class KeywordMatcher {
  constructor(config) {
    this.config = config;
    this.enabled = config.enabled !== false;
  }

  /**
   * Match snippet against notes using keyword matching
   * @param {import('../core/types.js').Snippet} snippet
   * @param {import('../core/types.js').Note[]} notes
   * @returns {Promise<import('../core/types.js').Match[]>}
   */
  async match(snippet, notes) {
    if (!this.enabled || !snippet.text) {
      return [];
    }

    const snippetText = normalize(snippet.text);

    // Extract keywords and n-grams from snippet
    const keywords = this.extractKeywords(snippetText);
    const bigrams = extractNGrams(snippetText, 2);
    const trigrams = extractNGrams(snippetText, 3);

    const allTerms = [...keywords, ...bigrams, ...trigrams];

    // Create corpus from all notes
    const corpus = notes.map(note =>
      this.extractKeywords(normalize(note.title + ' ' + note.content))
    );

    const matches = [];

    for (const note of notes) {
      const score = this.calculateMatchScore(
        allTerms,
        note,
        corpus,
        snippetText
      );

      if (score >= this.config.minScore) {
        const matchedTerms = this.findMatchedTerms(allTerms, note);
        matches.push({
          noteId: note.id,
          score,
          matcher: MatcherTypes.KEYWORD,
          reasoning: `Matched keywords: ${matchedTerms.slice(0, 5).join(', ')}`,
          matchedTerms
        });
      }
    }

    return matches.sort((a, b) => b.score - a.score);
  }

  /**
   * Calculate match score for a note
   * @private
   */
  calculateMatchScore(snippetTerms, note, corpus, snippetText) {
    const noteText = normalize(note.title + ' ' + note.content);
    const noteTerms = this.extractKeywords(noteText);

    let score = 0;
    const matchedTerms = new Set();

    for (const term of snippetTerms) {
      // Check if term appears in note
      if (noteText.includes(term)) {
        matchedTerms.add(term);

        // Calculate TF-IDF score
        const tfidf = calculateTFIDF(term, noteTerms, corpus);
        score += tfidf;

        // Bonus for title matches
        if (normalize(note.title).includes(term)) {
          score += tfidf * this.config.titleWeight;
        }

        // Bonus for exact phrase matches in original text
        if (snippetText.includes(term) && term.includes(' ')) {
          score += tfidf * this.config.phraseMatchBonus;
        }
      }
    }

    // Normalize score by number of terms to avoid bias toward long documents
    return matchedTerms.size > 0 ? score / snippetTerms.length : 0;
  }

  /**
   * Find which terms matched in a note
   * @private
   */
  findMatchedTerms(terms, note) {
    const noteText = normalize(note.title + ' ' + note.content);
    return terms.filter(term => noteText.includes(term));
  }

  /**
   * Extract keywords from text (removing stopwords)
   * @param {string} text
   * @returns {string[]}
   */
  extractKeywords(text) {
    const words = extractKeywords(text, this.config.minKeywordLength);
    return words.filter(word => !this.config.stopwords.includes(word));
  }
}
