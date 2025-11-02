import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Working example demonstrating the testing setup works

describe('Working Testing Example', () => {
  const user = userEvent.setup();

  it('should render a simple component', () => {
    const SimpleComponent = () => (
      <div data-testid="simple-component">
        <h1>Hello World</h1>
        <p>This is a test</p>
      </div>
    );

    render(<SimpleComponent />);
    
    expect(screen.getByTestId('simple-component')).toBeInTheDocument();
    expect(screen.getByText('Hello World')).toBeInTheDocument();
    expect(screen.getByText('This is a test')).toBeInTheDocument();
  });

  it('should handle user interactions', async () => {
    const InteractiveComponent = () => {
      const [count, setCount] = React.useState(0);
      
      return (
        <div data-testid="interactive-component">
          <span data-testid="count">{count}</span>
          <button 
            data-testid="increment-button"
            onClick={() => setCount(count + 1)}
          >
            Increment
          </button>
        </div>
      );
    };

    render(<InteractiveComponent />);
    
    const countElement = screen.getByTestId('count');
    const button = screen.getByTestId('increment-button');
    
    expect(countElement).toHaveTextContent('0');
    
    await user.click(button);
    expect(countElement).toHaveTextContent('1');
    
    await user.click(button);
    expect(countElement).toHaveTextContent('2');
  });

  it('should test form inputs', async () => {
    const FormComponent = () => {
      const [value, setValue] = React.useState('');
      
      return (
        <form data-testid="test-form">
          <input
            data-testid="test-input"
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Enter text"
          />
          <span data-testid="input-value">{value}</span>
        </form>
      );
    };

    render(<FormComponent />);
    
    const input = screen.getByTestId('test-input');
    const valueDisplay = screen.getByTestId('input-value');
    
    expect(input).toHaveValue('');
    expect(valueDisplay).toHaveTextContent('');
    
    await user.type(input, 'Hello World');
    
    expect(input).toHaveValue('Hello World');
    expect(valueDisplay).toHaveTextContent('Hello World');
  });

  it('should test conditional rendering', () => {
    const ConditionalComponent = ({ show = false }: { show?: boolean }) => (
      <div data-testid="conditional-component">
        {show && <span data-testid="conditional-content">Visible</span>}
        {!show && <span data-testid="hidden-content">Hidden</span>}
      </div>
    );

    // Test when show is false
    const { rerender } = render(<ConditionalComponent show={false} />);
    
    expect(screen.queryByTestId('conditional-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('hidden-content')).toBeInTheDocument();
    
    // Test when show is true
    rerender(<ConditionalComponent show={true} />);
    
    expect(screen.getByTestId('conditional-content')).toBeInTheDocument();
    expect(screen.queryByTestId('hidden-content')).not.toBeInTheDocument();
  });

  it('should test accessibility attributes', () => {
    const AccessibleComponent = () => (
      <div>
        <button 
          data-testid="accessible-button"
          aria-label="Close dialog"
          role="button"
        >
          ×
        </button>
        <input
          data-testid="accessible-input"
          type="text"
          aria-required="true"
          aria-describedby="input-help"
        />
        <span id="input-help">Please enter your name</span>
      </div>
    );

    render(<AccessibleComponent />);
    
    const button = screen.getByTestId('accessible-button');
    const input = screen.getByTestId('accessible-input');
    
    expect(button).toHaveAttribute('aria-label', 'Close dialog');
    expect(button).toHaveAttribute('role', 'button');
    expect(input).toHaveAttribute('aria-required', 'true');
    expect(input).toHaveAttribute('aria-describedby', 'input-help');
  });

  it('should test localStorage interactions', () => {
    // Test localStorage setup
    const StorageComponent = ({ value = '' }: { value?: string }) => (
      <div data-testid="storage-component">
        <span data-testid="storage-value">
          {value}
        </span>
      </div>
    );

    // Set localStorage before rendering
    localStorage.setItem('test-key', 'test-value');
    
    render(<StorageComponent value={localStorage.getItem('test-key') || ''} />);
    
    expect(screen.getByTestId('storage-value')).toHaveTextContent('test-value');
    expect(localStorage.getItem('test-key')).toBe('test-value');
  });

  it('should test async operations', async () => {
    const AsyncComponent = () => {
      const [data, setData] = React.useState<string>('');
      const [loading, setLoading] = React.useState(false);
      
      const fetchData = async () => {
        setLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 100));
        setData('Async data loaded');
        setLoading(false);
      };
      
      React.useEffect(() => {
        fetchData();
      }, []);
      
      return (
        <div data-testid="async-component">
          {loading && <span data-testid="loading">Loading...</span>}
          {data && <span data-testid="data">{data}</span>}
        </div>
      );
    };

    render(<AsyncComponent />);
    
    // Initially shows loading
    expect(screen.getByTestId('loading')).toBeInTheDocument();
    expect(screen.queryByTestId('data')).not.toBeInTheDocument();
    
    // Wait for async operation to complete
    expect(await screen.findByTestId('data')).toBeInTheDocument();
    expect(screen.getByTestId('data')).toHaveTextContent('Async data loaded');
    expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
  });
});
