import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as factories from '../factories';
import { testHelpers } from '../utils';

// Simple example demonstrating test data factories and utilities

describe('Simple Testing Example', () => {
  const user = userEvent.setup();

  describe('Factory Usage', () => {
    it('should create test users using factory', () => {
      const testUser = factories.userFactory.testUser();
      const freeUser = factories.userFactory.freeUser();
      const enterpriseUser = factories.userFactory.enterpriseUser();

      expect(testUser.email).toBe('test@example.com');
      expect(testUser.subscription.plan).toBe('pro');
      expect(freeUser.subscription.plan).toBe('free');
      expect(enterpriseUser.subscription.plan).toBe('enterprise');
    });

    it('should create multiple users using factory', () => {
      const users = factories.userFactory.buildMany(5);
      
      expect(users).toHaveLength(5);
      users.forEach(user => {
        expect(user).toHaveProperty('id');
        expect(user).toHaveProperty('email');
        expect(user).toHaveProperty('name');
        expect(user).toHaveProperty('preferences');
        expect(user).toHaveProperty('subscription');
      });
    });

    it('should create test chat data using factory', () => {
      const conversation = factories.chatFactory.testConversation();
      const messages = factories.chatFactory.createConversationHistory(3);

      expect(conversation.id).toBe('conv-test-1');
      expect(messages).toHaveLength(7); // 1 AI greeting + 3 user messages + 3 AI responses
      expect(messages[0].sender).toBe('ai');
      expect(messages[1].sender).toBe('user');
    });

    it('should create search results using factory', () => {
      const searchResponse = factories.searchFactory.searchForQuery('react testing', 5);

      expect(searchResponse.results).toHaveLength(5);
      expect(searchResponse.query).toBe('react testing');
      expect(searchResponse.results[0].title).toContain('react testing');
      expect(searchResponse.results[0].relevanceScore).toBeGreaterThan(0.9);
    });

    it('should create sentiment analysis using factory', () => {
      const positiveAnalysis = factories.sentimentFactory.positiveAnalysis();
      const negativeAnalysis = factories.sentimentFactory.negativeAnalysis();
      const neutralAnalysis = factories.sentimentFactory.neutralAnalysis();

      expect(positiveAnalysis.sentiment).toBe('positive');
      expect(negativeAnalysis.sentiment).toBe('negative');
      expect(neutralAnalysis.sentiment).toBe('neutral');
      
      // Test confidence scores
      expect(positiveAnalysis.confidence).toBeGreaterThan(0.8);
      expect(negativeAnalysis.confidence).toBeGreaterThan(0.8);
      expect(neutralAnalysis.confidence).toBeGreaterThan(0.7);
    });

    it('should create dashboard stats using factory', () => {
      const stats = factories.dashboardFactory.testStats();
      const emptyStats = factories.dashboardFactory.emptyStats();

      expect(stats.totalSearches).toBe(1250);
      expect(stats.popularQueries).toHaveLength(5);
      expect(emptyStats.totalSearches).toBe(0);
    });

    it('should create time series data using factory', () => {
      const weeklyData = factories.dashboardFactory.createWeeklyData();
      const monthlyData = factories.dashboardFactory.createMonthlyTrend(6);

      expect(weeklyData).toHaveLength(7);
      expect(monthlyData).toHaveLength(6);
      
      weeklyData.forEach(data => {
        expect(data).toHaveProperty('date');
        expect(data).toHaveProperty('searches');
        expect(data).toHaveProperty('conversations');
        expect(data).toHaveProperty('sentimentAnalyses');
      });
    });
  });

  describe('Test Helpers Usage', () => {
    it('should test localStorage interactions', () => {
      testHelpers.testLocalStorage.setItem('theme', 'dark');
      testHelpers.testLocalStorage.testItemExists('theme', 'dark');

      testHelpers.testLocalStorage.removeItem('theme');
      testHelpers.testLocalStorage.testItemNotExists('theme');
    });

    it('should test sessionStorage interactions', () => {
      testHelpers.testSessionStorage.setItem('tempData', 'temporary');
      testHelpers.testSessionStorage.testItemExists('tempData', 'temporary');

      testHelpers.testSessionStorage.clear();
      testHelpers.testSessionStorage.testItemNotExists('tempData');
    });

    it('should test async operations with delay', async () => {
      const startTime = Date.now();
      await testHelpers.delay(100);
      const endTime = Date.now();

      expect(endTime - startTime).toBeGreaterThanOrEqual(100);
    });

    it('should test element attributes', () => {
      const TestComponent = () => (
        <div>
          <button 
            data-testid="test-button"
            aria-label="Test button"
            role="button"
            disabled
          >
            Click me
          </button>
          <input 
            data-testid="test-input"
            type="text"
            placeholder="Enter text"
          />
        </div>
      );

      render(<TestComponent />);

      // Test button attributes
      testHelpers.testA11yAttributes('test-button', {
        'aria-label': 'Test button',
        'role': 'button',
      });

      testHelpers.testElementDisabled('test-button');

      // Test input attributes
      const input = screen.getByTestId('test-input');
      expect(input).toHaveAttribute('type', 'text');
      expect(input).toHaveAttribute('placeholder', 'Enter text');
    });

    it('should test text content', () => {
      const TestComponent = () => (
        <div data-testid="test-container">
          <h1>Welcome to the App</h1>
          <p>This is a test paragraph</p>
          <span>Additional content</span>
        </div>
      );

      render(<TestComponent />);

      testHelpers.testTextContent('test-container', 'Welcome to the App');
      testHelpers.testChildren('test-container', ['Welcome to the App', 'This is a test paragraph', 'Additional content']);
      testHelpers.testNotContainsText('test-container', 'Forbidden text');
    });

    it('should test responsive behavior', async () => {
      const ResponsiveSize = () => {
        const [size, setSize] = React.useState({
          width: window.innerWidth,
          height: window.innerHeight,
        });

        React.useEffect(() => {
          const handleResize = () => {
            setSize({ width: window.innerWidth, height: window.innerHeight });
          };
          window.addEventListener('resize', handleResize);
          return () => window.removeEventListener('resize', handleResize);
        }, []);

        return (
          <>
            <span data-testid="width-display">{size.width}px</span>
            <span data-testid="height-display">{size.height}px</span>
          </>
        );
      };

      const TestComponent = () => (
        <div data-testid="responsive-component">
          <ResponsiveSize />
        </div>
      );

      render(<TestComponent />);

      // Test mobile view
      await testHelpers.testResponsive('responsive-component', 375, 667);
      expect(screen.getByTestId('width-display')).toHaveTextContent('375px');
      expect(screen.getByTestId('height-display')).toHaveTextContent('667px');

      // Test desktop view
      await testHelpers.testResponsive('responsive-component', 1920, 1080);
      expect(screen.getByTestId('width-display')).toHaveTextContent('1920px');
      expect(screen.getByTestId('height-display')).toHaveTextContent('1080px');
    });
  });

  describe('Component Testing with Factories', () => {
    it('should test user profile component with factory data', () => {
      const UserProfile = ({ user }: { user: any }) => (
        <div data-testid="user-profile">
          <h2 data-testid="user-name">{user.name}</h2>
          <p data-testid="user-email">{user.email}</p>
          <span data-testid="user-plan">{user.subscription.plan}</span>
        </div>
      );

      const testUser = factories.userFactory.testUser();
      render(<UserProfile user={testUser} />);

      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
      expect(screen.getByTestId('user-plan')).toHaveTextContent('pro');
    });

    it('should test search results component with factory data', () => {
      const SearchResults = ({ results }: { results: any[] }) => (
        <div data-testid="search-results">
          {results.map(result => (
            <div key={result.id} data-testid={`result-${result.id}`}>
              <h3 data-testid={`result-title-${result.id}`}>{result.title}</h3>
              <p data-testid={`result-desc-${result.id}`}>{result.description}</p>
              <span data-testid={`result-score-${result.id}`}>{result.relevanceScore}</span>
            </div>
          ))}
        </div>
      );

      const searchResponse = factories.searchFactory.searchForQuery('react testing', 3);
      render(<SearchResults results={searchResponse.results} />);

      expect(screen.getByTestId('search-results')).toBeInTheDocument();
      expect(screen.getAllByTestId(/result-title-/)).toHaveLength(3);
      expect(screen.getByTestId('result-title-' + searchResponse.results[0].id))
        .toHaveTextContent('react testing');
    });

    it('should test sentiment display component with factory data', () => {
      const SentimentDisplay = ({ analysis }: { analysis: any }) => (
        <div data-testid="sentiment-display">
          <span data-testid="sentiment-type">{analysis.sentiment}</span>
          <span data-testid="sentiment-confidence">{analysis.confidence}</span>
          <div data-testid="sentiment-scores">
            <span data-testid="score-positive">{analysis.scores.positive}</span>
            <span data-testid="score-negative">{analysis.scores.negative}</span>
            <span data-testid="score-neutral">{analysis.scores.neutral}</span>
          </div>
        </div>
      );

      const analysis = factories.sentimentFactory.positiveAnalysis();
      render(<SentimentDisplay analysis={analysis} />);

      expect(screen.getByTestId('sentiment-type')).toHaveTextContent('positive');
      expect(screen.getByTestId('sentiment-confidence')).toHaveTextContent('0.92');
      expect(screen.getByTestId('score-positive')).toHaveTextContent('0.85');
    });
  });

  describe('Mock Function Testing', () => {
    it('should test API call mocking', () => {
      const mockApiCall = jest.fn().mockResolvedValue({
        success: true,
        data: { message: 'Mock response' }
      });

      expect(mockApiCall).not.toHaveBeenCalled();
      
      // Test the mock function
      mockApiCall('/api/test');
      
      expect(mockApiCall).toHaveBeenCalledWith('/api/test');
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });

    it('should test async mock functions', async () => {
      const mockAsyncCall = jest.fn().mockResolvedValue({
        success: true,
        data: { result: 'async result' }
      });

      const result = await mockAsyncCall('/api/async');
      
      expect(result).toEqual({
        success: true,
        data: { result: 'async result' }
      });
      expect(mockAsyncCall).toHaveBeenCalledWith('/api/async');
    });
  });
});
