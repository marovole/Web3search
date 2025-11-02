import { faker } from '@faker-js/faker';

export interface SentimentScore {
  positive: number;
  negative: number;
  neutral: number;
}

export interface EmotionScore {
  joy: number;
  anger: number;
  fear: number;
  sadness: number;
}

export interface SentimentAnalysis {
  id: string;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  scores: SentimentScore;
  emotions: EmotionScore;
  processedAt: string;
}

export const createSentimentFactory = () => ({
  buildAnalysis: (overrides: Partial<SentimentAnalysis> = {}): SentimentAnalysis => {
    const sentiment = faker.helpers.arrayElement(['positive', 'negative', 'neutral']);
    
    // Generate realistic scores based on sentiment
    let scores: SentimentScore;
    let emotions: EmotionScore;
    
    switch (sentiment) {
      case 'positive':
        scores = {
          positive: faker.number.float({ min: 0.7, max: 0.95, precision: 0.01 }),
          negative: faker.number.float({ min: 0.01, max: 0.15, precision: 0.01 }),
          neutral: faker.number.float({ min: 0.05, max: 0.25, precision: 0.01 }),
        };
        emotions = {
          joy: faker.number.float({ min: 0.6, max: 0.9, precision: 0.01 }),
          anger: faker.number.float({ min: 0.01, max: 0.1, precision: 0.01 }),
          fear: faker.number.float({ min: 0.01, max: 0.1, precision: 0.01 }),
          sadness: faker.number.float({ min: 0.05, max: 0.2, precision: 0.01 }),
        };
        break;
      case 'negative':
        scores = {
          positive: faker.number.float({ min: 0.01, max: 0.15, precision: 0.01 }),
          negative: faker.number.float({ min: 0.7, max: 0.95, precision: 0.01 }),
          neutral: faker.number.float({ min: 0.05, max: 0.25, precision: 0.01 }),
        };
        emotions = {
          joy: faker.number.float({ min: 0.01, max: 0.1, precision: 0.01 }),
          anger: faker.number.float({ min: 0.3, max: 0.8, precision: 0.01 }),
          fear: faker.number.float({ min: 0.1, max: 0.4, precision: 0.01 }),
          sadness: faker.number.float({ min: 0.2, max: 0.7, precision: 0.01 }),
        };
        break;
      default: // neutral
        scores = {
          positive: faker.number.float({ min: 0.2, max: 0.4, precision: 0.01 }),
          negative: faker.number.float({ min: 0.2, max: 0.4, precision: 0.01 }),
          neutral: faker.number.float({ min: 0.4, max: 0.7, precision: 0.01 }),
        };
        emotions = {
          joy: faker.number.float({ min: 0.2, max: 0.4, precision: 0.01 }),
          anger: faker.number.float({ min: 0.1, max: 0.3, precision: 0.01 }),
          fear: faker.number.float({ min: 0.1, max: 0.3, precision: 0.01 }),
          sadness: faker.number.float({ min: 0.2, max: 0.4, precision: 0.01 }),
        };
    }

    return {
      id: faker.string.uuid(),
      text: faker.lorem.paragraph(),
      sentiment,
      confidence: faker.number.float({ min: 0.7, max: 0.98, precision: 0.01 }),
      scores,
      emotions,
      processedAt: faker.date.recent().toISOString(),
      ...overrides,
    };
  },

  buildAnalyses: (count: number, overrides: Partial<SentimentAnalysis> = {}): SentimentAnalysis[] =>
    Array.from({ length: count }, () => this.buildAnalysis(overrides)),

  // Predefined test data
  positiveAnalysis: (text = 'I love this product!'): SentimentAnalysis => 
    this.buildAnalysis({
      id: 'sentiment-positive-1',
      text,
      sentiment: 'positive',
      confidence: 0.92,
      scores: {
        positive: 0.85,
        negative: 0.05,
        neutral: 0.10,
      },
      emotions: {
        joy: 0.75,
        anger: 0.05,
        fear: 0.05,
        sadness: 0.15,
      },
    }),

  negativeAnalysis: (text = 'This is terrible!'): SentimentAnalysis => 
    this.buildAnalysis({
      id: 'sentiment-negative-1',
      text,
      sentiment: 'negative',
      confidence: 0.88,
      scores: {
        positive: 0.05,
        negative: 0.85,
        neutral: 0.10,
      },
      emotions: {
        joy: 0.05,
        anger: 0.65,
        fear: 0.20,
        sadness: 0.10,
      },
    }),

  neutralAnalysis: (text = 'This is a product.'): SentimentAnalysis => 
    this.buildAnalysis({
      id: 'sentiment-neutral-1',
      text,
      sentiment: 'neutral',
      confidence: 0.75,
      scores: {
        positive: 0.25,
        negative: 0.25,
        neutral: 0.50,
      },
      emotions: {
        joy: 0.25,
        anger: 0.15,
        fear: 0.15,
        sadness: 0.45,
      },
    }),

  // Analyze specific text
  analyzeText: (text: string): SentimentAnalysis => {
    // Simple sentiment detection based on keywords
    const positiveWords = ['love', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic'];
    const negativeWords = ['hate', 'terrible', 'awful', 'bad', 'worst', 'horrible'];
    
    const lowerText = text.toLowerCase();
    const hasPositive = positiveWords.some(word => lowerText.includes(word));
    const hasNegative = negativeWords.some(word => lowerText.includes(word));
    
    let sentiment: 'positive' | 'negative' | 'neutral';
    if (hasPositive && !hasNegative) {
      sentiment = 'positive';
    } else if (hasNegative && !hasPositive) {
      sentiment = 'negative';
    } else {
      sentiment = 'neutral';
    }
    
    return this.buildAnalysis({
      text,
      sentiment,
      confidence: 0.8,
    });
  },

  // Create sentiment history
  createHistory: (days = 30): SentimentAnalysis[] => 
    Array.from({ length: days }, (_, index) => 
      this.buildAnalysis({
        processedAt: faker.date.past({ days: index }).toISOString(),
      })
    ),
});

export const sentimentFactory = createSentimentFactory();
