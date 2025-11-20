/**
 * Content-Type Specific Matcher
 * Different matching strategies for different content types (URL, code, timestamps, text)
 */

import { MatcherTypes, ContentTypes } from '../core/types.js';
import { normalize, fuzzySimilarity } from '../utils/text.js';

export class ContentTypeMatcher {
  constructor(config) {
    this.config = config;
    this.enabled = config.enabled !== false;
  }

  /**
   * Match snippet against notes using content-type specific strategies
   * @param {import('../core/types.js').Snippet} snippet
   * @param {import('../core/types.js').Note[]} notes
   * @returns {Promise<import('../core/types.js').Match[]>}
   */
  async match(snippet, notes) {
    if (!this.enabled || !snippet.text) {
      return [];
    }

    const contentType = this.detectContentType(snippet.text);

    switch (contentType) {
      case ContentTypes.URL:
        return this.matchURL(snippet, notes);
      case ContentTypes.CODE:
        return this.matchCode(snippet, notes);
      case ContentTypes.TIMESTAMP:
        return this.matchTimestamp(snippet, notes);
      default:
        return []; // Fallback to other matchers
    }
  }

  /**
   * Detect content type of text
   * @param {string} text
   * @returns {string}
   */
  detectContentType(text) {
    // Check for URL
    if (this.isURL(text)) {
      return ContentTypes.URL;
    }

    // Check for code
    if (this.isCode(text)) {
      return ContentTypes.CODE;
    }

    // Check for timestamp
    if (this.hasTimestamp(text)) {
      return ContentTypes.TIMESTAMP;
    }

    return ContentTypes.TEXT;
  }

  /**
   * Check if text is a URL
   * @private
   */
  isURL(text) {
    try {
      new URL(text.trim());
      return true;
    } catch {
      return /^https?:\/\//.test(text.trim());
    }
  }

  /**
   * Check if text contains code
   * @private
   */
  isCode(text) {
    const codeIndicators = [
      /function\s+\w+\s*\(/,
      /class\s+\w+/,
      /import\s+.*from/,
      /const\s+\w+\s*=/,
      /def\s+\w+\s*\(/,
      /public\s+\w+/,
      /#include\s+</,
      /\{\s*\n.*\n\s*\}/s
    ];

    return codeIndicators.some(pattern => pattern.test(text));
  }

  /**
   * Check if text has timestamp
   * @private
   */
  hasTimestamp(text) {
    const timestampPatterns = [
      /\d{4}-\d{2}-\d{2}/,
      /\d{1,2}\/\d{1,2}\/\d{4}/,
      /\d{1,2}:\d{2}:\d{2}/,
      /@\d{2}:\d{2}/
    ];

    return timestampPatterns.some(pattern => pattern.test(text));
  }

  /**
   * Match URL snippets
   * @private
   */
  async matchURL(snippet, notes) {
    if (!this.config.url?.enabled) return [];

    const url = snippet.text.trim();
    let domain, title;

    try {
      const urlObj = new URL(url);
      domain = urlObj.hostname;
    } catch {
      return [];
    }

    // Extract title from metadata if available
    title = snippet.metadata?.title;

    const matches = [];

    for (const note of notes) {
      let score = 0;
      const matchedTerms = [];

      // Match by domain
      if (this.config.url.matchDomain && note.content.includes(domain)) {
        score += this.config.url.domainWeight;
        matchedTerms.push(`domain: ${domain}`);
      }

      // Match by title
      if (title && this.config.url.titleWeight) {
        const titleInNote = normalize(note.title + ' ' + note.content).includes(normalize(title));
        if (titleInNote) {
          score += this.config.url.titleWeight;
          matchedTerms.push(`title: ${title}`);
        }
      }

      // Check if URL itself is in note
      if (note.content.includes(url)) {
        score += 2.0;
        matchedTerms.push('exact URL');
      }

      if (score > 0) {
        matches.push({
          noteId: note.id,
          score: Math.min(score / 5.0, 1.0), // Normalize to [0,1]
          matcher: MatcherTypes.CONTENT_TYPE,
          reasoning: `URL match: ${matchedTerms.join(', ')}`,
          matchedTerms
        });
      }
    }

    return matches.sort((a, b) => b.score - a.score);
  }

  /**
   * Match code snippets
   * @private
   */
  async matchCode(snippet, notes) {
    if (!this.config.code?.enabled) return [];

    const language = this.detectLanguage(snippet.text);
    const imports = this.extractImports(snippet.text);
    const names = this.extractNames(snippet.text);

    const matches = [];

    for (const note of notes) {
      let score = 0;
      const matchedTerms = [];

      // Match by language
      if (language && note.content.toLowerCase().includes(language.toLowerCase())) {
        score += this.config.code.languageWeight;
        matchedTerms.push(`language: ${language}`);
      }

      // Match by imports
      for (const imp of imports) {
        if (note.content.includes(imp)) {
          score += 0.5;
          matchedTerms.push(`import: ${imp}`);
        }
      }

      // Match by function/class names
      for (const name of names) {
        if (note.content.includes(name)) {
          score += 0.3;
          matchedTerms.push(`name: ${name}`);
        }
      }

      if (score > 0) {
        matches.push({
          noteId: note.id,
          score: Math.min(score / 3.0, 1.0),
          matcher: MatcherTypes.CONTENT_TYPE,
          reasoning: `Code match: ${matchedTerms.join(', ')}`,
          matchedTerms
        });
      }
    }

    return matches.sort((a, b) => b.score - a.score);
  }

  /**
   * Detect programming language
   * @private
   */
  detectLanguage(code) {
    if (/import\s+.*from/.test(code) || /const\s+\w+/.test(code)) return 'JavaScript';
    if (/def\s+\w+\(/.test(code)) return 'Python';
    if (/public\s+class/.test(code)) return 'Java';
    if (/#include\s+</.test(code)) return 'C/C++';
    if (/fn\s+\w+/.test(code)) return 'Rust';
    return null;
  }

  /**
   * Extract import statements
   * @private
   */
  extractImports(code) {
    const imports = [];
    const patterns = [
      /import\s+(?:.*\s+from\s+)?['"]([^'"]+)['"]/g,
      /require\(['"]([^'"]+)['"]\)/g,
      /from\s+(\w+)\s+import/g,
      /#include\s+[<"]([^>"]+)[>"]/g
    ];

    for (const pattern of patterns) {
      const matches = code.matchAll(pattern);
      for (const match of matches) {
        imports.push(match[1]);
      }
    }

    return imports;
  }

  /**
   * Extract function and class names
   * @private
   */
  extractNames(code) {
    const names = [];
    const patterns = [
      /function\s+(\w+)/g,
      /class\s+(\w+)/g,
      /def\s+(\w+)/g,
      /const\s+(\w+)\s*=/g,
      /let\s+(\w+)\s*=/g,
      /var\s+(\w+)\s*=/g
    ];

    for (const pattern of patterns) {
      const matches = code.matchAll(pattern);
      for (const match of matches) {
        names.push(match[1]);
      }
    }

    return names;
  }

  /**
   * Match timestamp-based snippets
   * @private
   */
  async matchTimestamp(snippet, notes) {
    if (!this.config.timestamp?.enabled) return [];

    const dates = this.extractDates(snippet.text);
    const times = this.extractTimes(snippet.text);

    const matches = [];

    for (const note of notes) {
      let score = 0;
      const matchedTerms = [];

      // Match by dates
      for (const date of dates) {
        if (note.content.includes(date)) {
          score += 1.0;
          matchedTerms.push(`date: ${date}`);
        }

        // Also check if note was created near this date
        const noteDate = note.createdAt?.toISOString().split('T')[0];
        if (noteDate === date) {
          score += 1.5;
          matchedTerms.push(`created on: ${date}`);
        }
      }

      // Match by times
      for (const time of times) {
        if (note.content.includes(time)) {
          score += 0.5;
          matchedTerms.push(`time: ${time}`);
        }
      }

      if (score > 0) {
        matches.push({
          noteId: note.id,
          score: Math.min(score / 2.0, 1.0),
          matcher: MatcherTypes.CONTENT_TYPE,
          reasoning: `Timestamp match: ${matchedTerms.join(', ')}`,
          matchedTerms
        });
      }
    }

    return matches.sort((a, b) => b.score - a.score);
  }

  /**
   * Extract dates from text
   * @private
   */
  extractDates(text) {
    const dates = [];
    const patterns = [
      /\d{4}-\d{2}-\d{2}/g,
      /\d{1,2}\/\d{1,2}\/\d{4}/g,
      /\d{1,2}-\d{1,2}-\d{4}/g
    ];

    for (const pattern of patterns) {
      const matches = text.matchAll(pattern);
      for (const match of matches) {
        dates.push(match[0]);
      }
    }

    return dates;
  }

  /**
   * Extract times from text
   * @private
   */
  extractTimes(text) {
    const times = [];
    const patterns = [
      /\d{1,2}:\d{2}:\d{2}/g,
      /\d{1,2}:\d{2}/g,
      /@\d{2}:\d{2}/g
    ];

    for (const pattern of patterns) {
      const matches = text.matchAll(pattern);
      for (const match of matches) {
        times.push(match[0]);
      }
    }

    return times;
  }
}
