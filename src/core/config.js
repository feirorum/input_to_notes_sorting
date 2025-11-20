/**
 * Default configuration for all matchers
 */

export const DEFAULT_CONFIG = {
  matchers: {
    keyword: {
      enabled: true,
      minScore: 0.1,
      titleWeight: 3.0,
      phraseMatchBonus: 2.0,
      minKeywordLength: 3,
      stopwords: [
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
        'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very'
      ]
    },

    semantic: {
      enabled: false, // Disabled by default (would require external dependencies)
      model: 'Xenova/all-MiniLM-L6-v2',
      minSimilarity: 0.5,
      useCache: true,
      batchSize: 32
    },

    rules: {
      enabled: true,
      rules: [],
      matchMode: 'all', // 'first' or 'all'
      allowOverride: true
    },

    ner: {
      enabled: true,
      entityWeights: {
        PROJECT: 3.0,
        PERSON: 2.0,
        ORG: 2.0,
        DATE: 1.0,
        LOCATION: 1.0,
        OTHER: 0.5
      },
      minEntityOverlap: 0.3,
      buildIndex: true
    },

    contentType: {
      enabled: true,
      url: {
        enabled: true,
        fetchMetadata: false, // Would require CORS proxy
        matchDomain: true,
        domainWeight: 2.0,
        titleWeight: 3.0
      },
      code: {
        enabled: true,
        languageDetection: true,
        extractImports: true,
        extractNames: true,
        languageWeight: 1.5
      },
      timestamp: {
        enabled: true,
        timeWindow: '7d',
        dateFormats: ['ISO', 'US', 'EU'],
        matchCalendar: false
      }
    },

    interactive: {
      enabled: true,
      confidenceThreshold: 0.7,
      maxSuggestions: 5,
      autoSortIfSingleMatch: false,
      rememberChoices: true
    },

    hybrid: {
      enabled: true,
      weights: {
        keyword: 1.0,
        semantic: 2.0,
        rules: 3.0,
        ner: 1.5,
        contentType: 1.5
      },
      normalizationMethod: 'minmax', // 'minmax' | 'zscore' | 'softmax'
      combineMethod: 'weighted-sum' // 'weighted-sum' | 'multiply' | 'max'
    }
  },

  demo: {
    showScoreBreakdown: true,
    showMatcherViz: true,
    enableDebugMode: true,
    animationSpeed: 300 // ms
  }
};

/**
 * Get current configuration (merges with localStorage overrides)
 */
export function getConfig() {
  try {
    const stored = localStorage.getItem('noteSortingConfig');
    if (stored) {
      return { ...DEFAULT_CONFIG, ...JSON.parse(stored) };
    }
  } catch (e) {
    console.warn('Failed to load config from localStorage:', e);
  }
  return DEFAULT_CONFIG;
}

/**
 * Save configuration to localStorage
 */
export function saveConfig(config) {
  try {
    localStorage.setItem('noteSortingConfig', JSON.stringify(config));
  } catch (e) {
    console.error('Failed to save config:', e);
  }
}

/**
 * Reset to default configuration
 */
export function resetConfig() {
  localStorage.removeItem('noteSortingConfig');
  return DEFAULT_CONFIG;
}
