/**
 * Text processing utilities
 */

/**
 * Remove stopwords from text
 * @param {string} text
 * @param {string[]} stopwords
 * @returns {string}
 */
export function removeStopwords(text, stopwords) {
  const words = text.toLowerCase().split(/\s+/);
  return words.filter(w => !stopwords.includes(w)).join(' ');
}

/**
 * Extract keywords from text
 * @param {string} text
 * @param {number} minLength
 * @returns {string[]}
 */
export function extractKeywords(text, minLength = 3) {
  return text
    .toLowerCase()
    .match(/\b\w+\b/g)
    ?.filter(word => word.length >= minLength) || [];
}

/**
 * Extract n-grams from text
 * @param {string} text
 * @param {number} n
 * @returns {string[]}
 */
export function extractNGrams(text, n = 2) {
  const words = text.toLowerCase().match(/\b\w+\b/g) || [];
  const ngrams = [];
  for (let i = 0; i <= words.length - n; i++) {
    ngrams.push(words.slice(i, i + n).join(' '));
  }
  return ngrams;
}

/**
 * Calculate term frequency
 * @param {string[]} terms
 * @returns {Map<string, number>}
 */
export function calculateTermFrequency(terms) {
  const freq = new Map();
  for (const term of terms) {
    freq.set(term, (freq.get(term) || 0) + 1);
  }
  return freq;
}

/**
 * Calculate TF-IDF score
 * @param {string} term
 * @param {string[]} document - document terms
 * @param {string[][]} corpus - all documents
 * @returns {number}
 */
export function calculateTFIDF(term, document, corpus) {
  // Term frequency in document
  const tf = document.filter(t => t === term).length / document.length;

  // Document frequency (how many documents contain this term)
  const df = corpus.filter(doc => doc.includes(term)).length;

  // Inverse document frequency
  const idf = df > 0 ? Math.log(corpus.length / df) : 0;

  return tf * idf;
}

/**
 * Calculate cosine similarity between two vectors
 * @param {number[]} vec1
 * @param {number[]} vec2
 * @returns {number}
 */
export function cosineSimilarity(vec1, vec2) {
  if (vec1.length !== vec2.length) return 0;

  let dotProduct = 0;
  let norm1 = 0;
  let norm2 = 0;

  for (let i = 0; i < vec1.length; i++) {
    dotProduct += vec1[i] * vec2[i];
    norm1 += vec1[i] * vec1[i];
    norm2 += vec2[i] * vec2[i];
  }

  const magnitude = Math.sqrt(norm1) * Math.sqrt(norm2);
  return magnitude === 0 ? 0 : dotProduct / magnitude;
}

/**
 * Normalize string for comparison
 * @param {string} str
 * @returns {string}
 */
export function normalize(str) {
  return str.toLowerCase().trim().replace(/\s+/g, ' ');
}

/**
 * Calculate Levenshtein distance between two strings
 * @param {string} str1
 * @param {string} str2
 * @returns {number}
 */
export function levenshteinDistance(str1, str2) {
  const m = str1.length;
  const n = str2.length;
  const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (str1[i - 1] === str2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(
          dp[i - 1][j],     // deletion
          dp[i][j - 1],     // insertion
          dp[i - 1][j - 1]  // substitution
        );
      }
    }
  }

  return dp[m][n];
}

/**
 * Calculate fuzzy similarity (normalized Levenshtein)
 * @param {string} str1
 * @param {string} str2
 * @returns {number} - similarity score [0, 1]
 */
export function fuzzySimilarity(str1, str2) {
  const distance = levenshteinDistance(str1, str2);
  const maxLength = Math.max(str1.length, str2.length);
  return maxLength === 0 ? 1 : 1 - (distance / maxLength);
}
