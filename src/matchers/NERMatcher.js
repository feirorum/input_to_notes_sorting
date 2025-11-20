/**
 * Named Entity Recognition Matcher
 * Extracts and matches based on entities (people, projects, organizations, etc.)
 */

import { MatcherTypes, EntityTypes } from '../core/types.js';

export class NERMatcher {
  constructor(config) {
    this.config = config;
    this.enabled = config.enabled !== false;
    this.entityIndex = null;
  }

  /**
   * Match snippet against notes using entity extraction
   * @param {import('../core/types.js').Snippet} snippet
   * @param {import('../core/types.js').Note[]} notes
   * @returns {Promise<import('../core/types.js').Match[]>}
   */
  async match(snippet, notes) {
    if (!this.enabled || !snippet.text) {
      return [];
    }

    // Extract entities from snippet
    const snippetEntities = this.extractEntities(snippet.text);

    // Build entity index if needed
    if (!this.entityIndex || this.config.buildIndex) {
      this.entityIndex = this.buildEntityIndex(notes);
    }

    const matches = [];

    for (const note of notes) {
      const noteEntities = this.entityIndex.get(note.id) || [];
      const score = this.calculateEntityOverlap(snippetEntities, noteEntities);

      if (score >= this.config.minEntityOverlap) {
        const matchedEntities = this.findMatchedEntities(snippetEntities, noteEntities);
        matches.push({
          noteId: note.id,
          score,
          matcher: MatcherTypes.NER,
          reasoning: `Matched entities: ${matchedEntities.map(e => `${e.text} (${e.type})`).join(', ')}`,
          matchedTerms: matchedEntities.map(e => e.text)
        });
      }
    }

    return matches.sort((a, b) => b.score - a.score);
  }

  /**
   * Extract entities from text using pattern matching
   * @param {string} text
   * @returns {import('../core/types.js').Entity[]}
   */
  extractEntities(text) {
    const entities = [];

    // Extract PROJECT entities (uppercase acronyms or "X project")
    const projectMatches = [
      ...text.matchAll(/\b([A-Z]{2,})\b/g),
      ...text.matchAll(/\b(\w+)\s+project\b/gi)
    ];
    for (const match of projectMatches) {
      entities.push({
        text: match[1],
        type: EntityTypes.PROJECT,
        startPos: match.index,
        endPos: match.index + match[0].length,
        confidence: 0.8
      });
    }

    // Extract PERSON entities (capitalized names)
    const personMatches = text.matchAll(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b/g);
    const commonWords = new Set(['I', 'The', 'A', 'An', 'This', 'That', 'We', 'Sam', 'Emma', 'Alex']);
    for (const match of personMatches) {
      const name = match[1];
      // Filter out common words that aren't names
      if (!commonWords.has(name.split(' ')[0])) {
        entities.push({
          text: name,
          type: EntityTypes.PERSON,
          startPos: match.index,
          endPos: match.index + match[0].length,
          confidence: 0.6
        });
      } else if (commonWords.has(name)) {
        // Known person names
        entities.push({
          text: name,
          type: EntityTypes.PERSON,
          startPos: match.index,
          endPos: match.index + match[0].length,
          confidence: 0.9
        });
      }
    }

    // Extract DATE entities
    const dateMatches = [
      ...text.matchAll(/\b(\d{4}-\d{2}-\d{2})\b/g),
      ...text.matchAll(/\b(\d{1,2}\/\d{1,2}\/\d{4})\b/g),
      ...text.matchAll(/\b(\d{1,2}-\d{1,2}-\d{4})\b/g)
    ];
    for (const match of dateMatches) {
      entities.push({
        text: match[1],
        type: EntityTypes.DATE,
        startPos: match.index,
        endPos: match.index + match[0].length,
        confidence: 1.0
      });
    }

    // Extract ORG entities (Inc., Corp., LLC, etc.)
    const orgMatches = text.matchAll(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|LLC|Ltd)\b/g);
    for (const match of orgMatches) {
      entities.push({
        text: match[0],
        type: EntityTypes.ORG,
        startPos: match.index,
        endPos: match.index + match[0].length,
        confidence: 0.9
      });
    }

    return entities;
  }

  /**
   * Build entity index for all notes
   * @param {import('../core/types.js').Note[]} notes
   * @returns {Map<string, import('../core/types.js').Entity[]>}
   */
  buildEntityIndex(notes) {
    const index = new Map();

    for (const note of notes) {
      const text = note.title + ' ' + note.content;
      const entities = this.extractEntities(text);
      index.set(note.id, entities);

      // Cache in note metadata if possible
      if (!note.metadata) note.metadata = {};
      note.metadata.entities = entities;
    }

    return index;
  }

  /**
   * Calculate entity overlap score between two entity sets
   * @param {import('../core/types.js').Entity[]} entities1
   * @param {import('../core/types.js').Entity[]} entities2
   * @returns {number}
   */
  calculateEntityOverlap(entities1, entities2) {
    if (entities1.length === 0 || entities2.length === 0) return 0;

    const matched = this.findMatchedEntities(entities1, entities2);
    if (matched.length === 0) return 0;

    // Calculate weighted score
    let score = 0;
    for (const entity of matched) {
      const weight = this.config.entityWeights[entity.type] || 1.0;
      score += weight;
    }

    // Normalize by total entities
    const maxPossibleScore = Math.min(entities1.length, entities2.length) *
      Math.max(...Object.values(this.config.entityWeights));

    return maxPossibleScore > 0 ? score / maxPossibleScore : 0;
  }

  /**
   * Find entities that match between two sets
   * @param {import('../core/types.js').Entity[]} entities1
   * @param {import('../core/types.js').Entity[]} entities2
   * @returns {import('../core/types.js').Entity[]}
   */
  findMatchedEntities(entities1, entities2) {
    const matched = [];

    for (const e1 of entities1) {
      for (const e2 of entities2) {
        if (e1.type === e2.type && e1.text.toLowerCase() === e2.text.toLowerCase()) {
          matched.push(e1);
          break;
        }
      }
    }

    return matched;
  }

  /**
   * Get all entities of a specific type from text
   * @param {string} text
   * @param {string} type
   * @returns {import('../core/types.js').Entity[]}
   */
  getEntitiesByType(text, type) {
    const entities = this.extractEntities(text);
    return entities.filter(e => e.type === type);
  }
}
