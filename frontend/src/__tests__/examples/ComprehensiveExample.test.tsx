import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { factories, testHelpers, mockHelpers, a11yHelpers } from '../utils';
import { ThemeToggle } from '../../components/theme-toggle';

// Example demonstrating comprehensive testing setup

describe('Comprehensive Testing Example', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset mocks before each test
    mockHelpers.reset();
  });

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
    });

    it('should create sentiment analysis using factory', () => {
      const positiveAnalysis = factories.sentimentFactory.positiveAnalysis();
      const negativeAnalysis = factories.sentimentFactory.negativeAnalysis();
      const neutralAnalysis = factories.sentimentFactory.neutralAnalysis();

      expect(positiveAnalysis.sentiment).toBe('positive');
      expect(negativeAnalysis.sentiment).toBe('negative');
      expect(neutralAnalysis.sentiment).toBe('neutral');
    });

    it('should create dashboard stats using factory', () => {
      const stats = factories.dashboardFactory.testStats();
      const emptyStats = factories.dashboardFactory.emptyStats();

      expect(stats.totalSearches).toBe(1250);
      expect(stats.popularQueries).toHaveLength(5);
      expect(emptyStats.totalSearches).toBe(0);
    });
  });

  describe('Mock Helpers Usage', () => {
    it('should mock successful API response', async () => {
      const mockData = { message: 'Success!' };
      mockHelpers.mockSuccess('/api/test', mockData);

      // Test would make API call and receive mocked response
      const response = await fetch('/api/test');
      const data = await response.json();
      
      expect(data.success).toBe(true);
      expect(data.data).toEqual(mockData);
    });

    it('should mock error API response', async () => {
      mockHelpers.mockError('/api/test', 'Something went wrong', 500);

      try {
        const response = await fetch('/api/test');
        if (!response.ok) {
          const errorData = await response.json();
          expect(errorData.success).toBe(false);
          expect(errorData.error).toBe('Something went wrong');
        }
      } catch (error) {
        // Handle network errors or other exceptions
      }
    });

    it('should mock delayed response', async () => {
      const mockData = { message: 'Delayed response' };
      mockHelpers.mockDelay('/api/slow', 1000, mockData);

      const startTime = Date.now();
      const response = await fetch('/api/slow');
      const data = await response.json();
      const endTime = Date.now();

      expect(data.success).toBe(true);
      expect(endTime - startTime).toBeGreaterThanOrEqual(1000);
    });

    it('should mock authentication', async () => {
      const userData = factories.userFactory.testUser();
      mockHelpers.mockAuth.login(userData);

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com', password: 'password' }),
      });
      
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.data.user).toEqual(userData);
      expect(data.data.token).toBe('mock-jwt-token');
    });
  });

  describe('Test Helpers Usage', () => {
    it('should test form filling and submission', async () => {
      // Mock form component
      const TestForm = () => (
        <form data-testid="test-form">
          <input data-testid="email-input" type="email" />
          <input data-testid="password-input" type="password" />
          <button data-testid="submit-button" type="submit">Submit</button>
        </form>
      );

      render(<TestForm />);

      // Fill form using helper
      await testHelpers.fillForm({
        'email-input': 'test@example.com',
        'password-input': 'password123',
      });

      // Test form values
      expect(screen.getByTestId('email-input')).toHaveValue('test@example.com');
      expect(screen.getByTestId('password-input')).toHaveValue('password123');
    });

    it('should test loading states', async () => {
      const TestComponent = () => {
        const [loading, setLoading] = React.useState(true);
        
        React.useEffect(() => {
          setTimeout(() => setLoading(false), 100);
        }, []);

        return loading ? (
          <div data-testid="loading">Loading...</div>
        ) : (
          <div data-testid="content">Content loaded</div>
        );
      };

      render(<TestComponent />);

      // Wait for loading to complete
      expect(screen.getByTestId('loading')).toBeInTheDocument();
      await testHelpers.waitForLoadingToComplete('loading');
      expect(screen.getByTestId('content')).toBeInTheDocument();
    });

    it('should test error messages', async () => {
      const TestComponent = () => {
        const [error, setError] = React.useState('');
        
        React.useEffect(() => {
          setTimeout(() => setError('Something went wrong'), 100);
        }, []);

        return error ? (
          <div data-testid="error-message">{error}</div>
        ) : (
          <div>No error</div>
        );
      };

      render(<TestComponent />);

      await testHelpers.testErrorMessage('Something went wrong');
    });

    it('should test accessibility attributes', () => {
      const TestButton = () => (
        <button 
          data-testid="test-button"
          aria-label="Test button"
          role="button"
        >
          Click me
        </button>
      );

      render(<TestButton />);

      testHelpers.testA11yAttributes('test-button', {
        'aria-label': 'Test button',
        'role': 'button',
      });
    });
  });

  describe('Accessibility Testing', () => {
    it('should pass accessibility tests', async () => {
      const AccessibleComponent = () => (
        <main>
          <h1>Page Title</h1>
          <button aria-label="Close dialog">×</button>
          <form>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" required />
            <button type="submit">Submit</button>
          </form>
        </main>
      );

      await a11yHelpers.testAccessibility(<AccessibleComponent />);
    });

    it('should test button accessibility', () => {
      const TestButton = () => (
        <button data-testid="test-button" aria-label="Test button">
          Click me
        </button>
      );

      render(<TestButton />);
      a11yHelpers.testButtonAccessibility('test-button', 'Test button');
    });

    it('should test input accessibility', () => {
      const TestInput = () => (
        <div>
          <label htmlFor="test-input">Test Input</label>
          <input 
            data-testid="test-input" 
            id="test-input" 
            type="text" 
            required 
          />
        </div>
      );

      render(<TestInput />);
      a11yHelpers.testInputAccessibility('test-input', 'Test Input', true);
    });
  });

  describe('Integration with Existing Component', () => {
    it('should test ThemeToggle with comprehensive setup', async () => {
      // Mock localStorage
      const localStorageMock = {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      };
      Object.defineProperty(window, 'localStorage', { value: localStorageMock });

      render(<ThemeToggle />);

      // Test accessibility
      await a11yHelpers.testAccessibility(<ThemeToggle />);

      // Test button accessibility
      a11yHelpers.testButtonAccessibility('button', '切换主题');

      // Test theme switching
      const button = screen.getByRole('button');
      await user.click(button);

      // Test that dropdown appears
      expect(screen.getByText('浅色')).toBeInTheDocument();
      expect(screen.getByText('深色')).toBeInTheDocument();
      expect(screen.getByText('跟随系统')).toBeInTheDocument();

      // Test theme selection
      await user.click(screen.getByText('深色'));
      expect(document.documentElement).toHaveClass('dark');
    });
  });

  describe('Performance and Utilities', () => {
    it('should test responsive behavior', async () => {
      const TestComponent = () => (
        <div data-testid="responsive-component">
          <span data-testid="width-display">{window.innerWidth}px</span>
        </div>
      );

      render(<TestComponent />);

      // Test mobile view
      await testHelpers.testResponsive('responsive-component', 375, 667);
      expect(screen.getByTestId('width-display')).toHaveTextContent('375px');

      // Test desktop view
      await testHelpers.testResponsive('responsive-component', 1920, 1080);
      expect(screen.getByTestId('width-display')).toHaveTextContent('1920px');
    });

    it('should test localStorage interactions', () => {
      testHelpers.testLocalStorage.setItem('theme', 'dark');
      testHelpers.testLocalStorage.testItemExists('theme', 'dark');

      testHelpers.testLocalStorage.removeItem('theme');
      testHelpers.testLocalStorage.testItemNotExists('theme');
    });

    it('should test async operations with delay', async () => {
      const startTime = Date.now();
      await testHelpers.delay(500);
      const endTime = Date.now();

      expect(endTime - startTime).toBeGreaterThanOrEqual(500);
    });
  });
});
