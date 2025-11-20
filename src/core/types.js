/**
 * Core type definitions and interfaces for the note sorting system
 */

/**
 * @typedef {Object} Snippet
 * @property {string} id - Unique identifier
 * @property {string} text - The snippet content
 * @property {string} [source] - Source of snippet (podcast, youtube, manual, etc)
 * @property {Date} timestamp - When the snippet was created
 * @property {Object} [metadata] - Additional metadata
 * @property {string} [metadata.url] - Associated URL
 * @property {string} [metadata.title] - Title if available
 * @property {string} [metadata.author] - Author if available
 */

/**
 * @typedef {Object} Note
 * @property {string} id - Unique identifier
 * @property {string} title - Note title
 * @property {string} content - Note content
 * @property {Date} createdAt - Creation timestamp
 * @property {Date} updatedAt - Last update timestamp
 * @property {string[]} [tags] - Associated tags
 * @property {string} [category] - Category name
 * @property {Object} [metadata] - Additional metadata
 * @property {Float32Array} [metadata.embedding] - Cached embedding vector
 * @property {Entity[]} [metadata.entities] - Extracted entities
 */

/**
 * @typedef {Object} Match
 * @property {string} noteId - ID of the matched note
 * @property {number} score - Match score [0, 1]
 * @property {string} matcher - Which matcher produced this result
 * @property {string} [reasoning] - Human-readable explanation
 * @property {string[]} [matchedTerms] - Keywords, entities, etc that matched
 * @property {number} [confidence] - Confidence score (can differ from score)
 */

/**
 * @typedef {Object} Entity
 * @property {string} text - The entity text
 * @property {('PERSON'|'ORG'|'PROJECT'|'DATE'|'LOCATION'|'OTHER')} type - Entity type
 * @property {number} startPos - Start position in text
 * @property {number} endPos - End position in text
 * @property {number} [confidence] - Confidence score
 */

/**
 * @typedef {Object} MatcherConfig
 * @property {boolean} enabled - Whether this matcher is enabled
 * @property {Object} [options] - Matcher-specific options
 */

/**
 * @typedef {Object} SystemConfig
 * @property {Object} matchers - Matcher configurations
 * @property {MatcherConfig} matchers.keyword - Keyword matcher config
 * @property {MatcherConfig} matchers.semantic - Semantic matcher config
 * @property {MatcherConfig} matchers.rules - Rule-based matcher config
 * @property {MatcherConfig} matchers.ner - NER matcher config
 * @property {MatcherConfig} matchers.contentType - Content-type matcher config
 * @property {MatcherConfig} matchers.interactive - Interactive disambiguation config
 * @property {MatcherConfig} matchers.hybrid - Hybrid scorer config
 */

export const MatcherTypes = {
  KEYWORD: 'keyword',
  SEMANTIC: 'semantic',
  RULES: 'rules',
  NER: 'ner',
  CONTENT_TYPE: 'content-type',
  INTERACTIVE: 'interactive',
  HYBRID: 'hybrid'
};

export const EntityTypes = {
  PERSON: 'PERSON',
  ORG: 'ORG',
  PROJECT: 'PROJECT',
  DATE: 'DATE',
  LOCATION: 'LOCATION',
  OTHER: 'OTHER'
};

export const ContentTypes = {
  URL: 'url',
  CODE: 'code',
  TIMESTAMP: 'timestamp',
  TEXT: 'text'
};
