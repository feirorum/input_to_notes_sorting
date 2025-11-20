/**
 * Test data for demo
 */

/**
 * Example notes
 */
export const exampleNotes = [
  {
    id: 'note-1',
    title: 'Family Shoe Sizes',
    content: `Tracking shoe sizes for the family:
- Sam: 32 (measured March 2023)
- Emma: 28 (measured March 2023)
- Alex: 36 (measured February 2023)

Need to update before school shopping in August.`,
    createdAt: new Date('2023-03-15'),
    updatedAt: new Date('2023-03-15'),
    tags: ['family', 'shopping'],
    category: 'Personal'
  },

  {
    id: 'note-2',
    title: 'XYZ Project Notes',
    content: `XYZ Project - Security Integration

Status: Waiting for security team input
Timeline: Q2 2024

Tasks:
- Get security requirements ✓
- Implement authentication
- Code review
- Deploy to staging

Contact: security@company.com`,
    createdAt: new Date('2024-01-10'),
    updatedAt: new Date('2024-01-20'),
    tags: ['work', 'xyz', 'security'],
    category: 'Work'
  },

  {
    id: 'note-3',
    title: 'Podcast: The AI Revolution',
    content: `Podcast notes from "The AI Revolution" episode #42

Host: Dr. Sarah Chen
Date: 2024-01-15
URL: https://airevolution.podcast/ep42

Key points:
- Large language models are transforming software development
- Importance of understanding limitations
- Ethics in AI deployment

Timestamp @15:30 - Discussion about prompt engineering
Timestamp @28:45 - Future predictions

Related: Machine Learning course notes`,
    createdAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-01-15'),
    tags: ['podcast', 'ai', 'tech'],
    category: 'Learning'
  },

  {
    id: 'note-4',
    title: 'JavaScript Best Practices',
    content: `JavaScript coding standards for our team

Import conventions:
- Use named imports for utilities
- Default imports for components
- Example: import { formatDate } from './utils'

Function naming:
- Use camelCase
- Start with verb (get, set, create, etc.)

Code review checklist:
- No console.log statements
- Proper error handling
- TypeScript types defined`,
    createdAt: new Date('2023-12-01'),
    updatedAt: new Date('2024-01-05'),
    tags: ['javascript', 'coding', 'standards'],
    category: 'Work'
  },

  {
    id: 'note-5',
    title: 'Weekly Team Meeting Notes',
    content: `Team meeting - January 22, 2024

Attendees: Sam, Emma, John, Sarah
Time: 10:00 AM

Agenda:
1. Sprint review
2. Blocker discussion
3. Next sprint planning

Action items:
- Sam: Update documentation
- Emma: Review pull requests
- John: Fix production bug
- Sarah: Schedule training session`,
    createdAt: new Date('2024-01-22'),
    updatedAt: new Date('2024-01-22'),
    tags: ['meeting', 'team', 'work'],
    category: 'Work'
  },

  {
    id: 'note-6',
    title: 'Recipe: Chocolate Cake',
    content: `Best chocolate cake recipe

Ingredients:
- 2 cups flour
- 1.5 cups sugar
- 3/4 cup cocoa powder
- 2 eggs
- 1 cup milk

Instructions:
1. Preheat oven to 350°F
2. Mix dry ingredients
3. Add wet ingredients
4. Bake for 30 minutes

Source: https://recipes.com/chocolate-cake
Tried: 2023-12-25 (Christmas)
Rating: 5/5 stars`,
    createdAt: new Date('2023-12-20'),
    updatedAt: new Date('2023-12-26'),
    tags: ['recipe', 'cooking', 'dessert'],
    category: 'Personal'
  },

  {
    id: 'note-7',
    title: 'Book Notes: Clean Code',
    content: `Reading notes from "Clean Code" by Robert Martin

Chapter 3: Functions
- Functions should be small
- Do one thing
- Use descriptive names
- Minimize arguments

Chapter 5: Formatting
- Team should agree on formatting rules
- Vertical formatting matters
- Use whitespace meaningfully

Great book for improving code quality.
Recommended by Sarah during code review.`,
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-10'),
    tags: ['book', 'programming', 'learning'],
    category: 'Learning'
  }
];

/**
 * Example snippets to test matching
 */
export const exampleSnippets = [
  {
    id: 'snippet-1',
    text: "Sam's shoe size is now 34",
    source: 'manual',
    timestamp: new Date('2024-01-25'),
    metadata: {
      description: 'Should match "Family Shoe Sizes" note'
    }
  },

  {
    id: 'snippet-2',
    text: 'We got the input needed from security, on the XYZ project',
    source: 'manual',
    timestamp: new Date('2024-01-25'),
    metadata: {
      description: 'Should match "XYZ Project Notes"'
    }
  },

  {
    id: 'snippet-3',
    text: `Podcast note from AI Revolution podcast @15:30 -
They discussed how prompt engineering is becoming a critical skill.
The examples about few-shot learning were particularly interesting.`,
    source: 'podcast',
    timestamp: new Date('2024-01-15'),
    metadata: {
      url: 'https://airevolution.podcast/ep42',
      title: 'The AI Revolution - Episode 42',
      description: 'Should match "Podcast: The AI Revolution" note'
    }
  },

  {
    id: 'snippet-4',
    text: `function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}`,
    source: 'manual',
    timestamp: new Date('2024-01-25'),
    metadata: {
      description: 'Code snippet - should match "JavaScript Best Practices"'
    }
  },

  {
    id: 'snippet-5',
    text: 'Emma mentioned she needs help with the pull request reviews',
    source: 'manual',
    timestamp: new Date('2024-01-25'),
    metadata: {
      description: 'Should match "Weekly Team Meeting Notes" or work-related notes'
    }
  },

  {
    id: 'snippet-6',
    text: 'Tried the chocolate recipe again, used 2 cups of sugar instead - even better!',
    source: 'manual',
    timestamp: new Date('2024-01-26'),
    metadata: {
      description: 'Should match "Recipe: Chocolate Cake"'
    }
  },

  {
    id: 'snippet-7',
    text: 'https://github.com/user/clean-code-examples - Great examples of the principles from Clean Code book',
    source: 'manual',
    timestamp: new Date('2024-01-26'),
    metadata: {
      url: 'https://github.com/user/clean-code-examples',
      title: 'Clean Code Examples',
      description: 'URL snippet - should match "Book Notes: Clean Code"'
    }
  },

  {
    id: 'snippet-8',
    text: 'Schedule next team meeting for January 29, 2024 at 10:00 AM',
    source: 'manual',
    timestamp: new Date('2024-01-26'),
    metadata: {
      description: 'Date/time reference - should match "Weekly Team Meeting Notes"'
    }
  }
];

/**
 * Example rules for rule-based matcher
 */
export const exampleRules = [
  {
    id: 'rule-1',
    name: 'XYZ Project Rule',
    noteId: 'note-2',
    priority: 1,
    conditions: {
      type: 'OR',
      rules: [
        { type: 'keyword', value: 'xyz', caseSensitive: false },
        { type: 'regex', value: 'xyz.*project', caseSensitive: false },
        { type: 'contains', value: 'security', caseSensitive: false }
      ]
    }
  },

  {
    id: 'rule-2',
    name: 'Podcast Rule',
    noteId: 'note-3',
    priority: 2,
    conditions: {
      type: 'OR',
      rules: [
        { type: 'keyword', value: 'podcast', caseSensitive: false },
        { type: 'regex', value: '@\\d{2}:\\d{2}', caseSensitive: false },
        { type: 'contains', value: 'episode', caseSensitive: false }
      ]
    }
  },

  {
    id: 'rule-3',
    name: 'Family Sizes Rule',
    noteId: 'note-1',
    priority: 1,
    conditions: {
      type: 'AND',
      rules: [
        { type: 'regex', value: '(sam|emma|alex)', caseSensitive: false },
        { type: 'regex', value: 'shoe|size', caseSensitive: false }
      ]
    }
  },

  {
    id: 'rule-4',
    name: 'Code Snippet Rule',
    noteId: 'note-4',
    priority: 2,
    conditions: {
      type: 'OR',
      rules: [
        { type: 'keyword', value: 'function', caseSensitive: true },
        { type: 'keyword', value: 'const', caseSensitive: true },
        { type: 'regex', value: 'import.*from', caseSensitive: false }
      ]
    }
  }
];
