import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

// Create a simple SearchBar component for testing
interface SearchBarProps {
  onSearch: (query: string) => void
  placeholder?: string
  disabled?: boolean
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, placeholder = 'Search...', disabled = false }) => {
  const [query, setQuery] = React.useState('')
  const [suggestions, setSuggestions] = React.useState<string[]>([])
  const [isLoading, setIsLoading] = React.useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)
    
    // Mock suggestion loading
    if (value.length > 0) {
      setIsLoading(true)
      setTimeout(() => {
        const mockSuggestions = [
          `${value} price analysis`,
          `${value} market trends`,
          `${value} technical indicators`,
        ].filter(s => s.toLowerCase().includes(value.toLowerCase()))
        setSuggestions(mockSuggestions.slice(0, 3))
        setIsLoading(false)
      }, 100)
    } else {
      setSuggestions([])
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && !disabled) {
      onSearch(query.trim())
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    setSuggestions([])
    onSearch(suggestion)
  }

  return (
    <div className="search-bar" data-testid="search-bar">
      <form onSubmit={handleSubmit} data-testid="search-form">
        <div className="search-input-container" data-testid="search-input-container">
          <input
            data-testid="search-input"
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder={placeholder}
            disabled={disabled}
            className="search-input"
          />
          <button
            data-testid="search-button"
            type="submit"
            disabled={disabled || !query.trim()}
            className="search-button"
          >
            Search
          </button>
        </div>
        
        {isLoading && (
          <div data-testid="search-loading">Loading suggestions...</div>
        )}
        
        {suggestions.length > 0 && (
          <div data-testid="search-suggestions" className="suggestions-list">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                data-testid={`suggestion-${index}`}
                onClick={() => handleSuggestionClick(suggestion)}
                className="suggestion-item"
                type="button"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </form>
    </div>
  )
}

describe('SearchBar', () => {
  const mockOnSearch = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic functionality', () => {
    it('should render search input and button', () => {
      render(<SearchBar onSearch={mockOnSearch} />)
      
      expect(screen.getByTestId('search-bar')).toBeInTheDocument()
      expect(screen.getByTestId('search-input')).toBeInTheDocument()
      expect(screen.getByTestId('search-button')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument()
    })

    it('should use custom placeholder', () => {
      render(<SearchBar onSearch={mockOnSearch} placeholder="Search coins, tokens..." />)
      
      expect(screen.getByPlaceholderText('Search coins, tokens...')).toBeInTheDocument()
    })

    it('should disable input and button when disabled prop is true', () => {
      render(<SearchBar onSearch={mockOnSearch} disabled={true} />)
      
      expect(screen.getByTestId('search-input')).toBeDisabled()
      expect(screen.getByTestId('search-button')).toBeDisabled()
    })
  })

  describe('Input handling', () => {
    it('should update input value when typing', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, 'Bitcoin')
      
      expect(input).toHaveValue('Bitcoin')
    })

    it('should show loading state while fetching suggestions', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, 'BTC')
      
      expect(screen.getByTestId('search-loading')).toBeInTheDocument()
      expect(screen.getByText('Loading suggestions...')).toBeInTheDocument()
    })

    it('should show suggestions after typing', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)

      const input = screen.getByTestId('search-input')
      await user.type(input, 'BTC')

      await waitFor(() => {
        expect(screen.getByTestId('search-suggestions')).toBeInTheDocument()
        expect(screen.getByTestId('suggestion-0')).toBeInTheDocument()
        expect(screen.getByText('BTC price analysis')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should clear suggestions when input is cleared', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)

      const input = screen.getByTestId('search-input')
      await user.type(input, 'BTC')

      await waitFor(() => {
        expect(screen.getByTestId('search-suggestions')).toBeInTheDocument()
      }, { timeout: 3000 })

      // Clear input
      await user.clear(input)

      expect(screen.queryByTestId('search-suggestions')).not.toBeInTheDocument()
    })
  })

  describe('Search functionality', () => {
    it('should call onSearch when form is submitted', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, 'Ethereum')
      
      const form = screen.getByTestId('search-form')
      fireEvent.submit(form)
      
      expect(mockOnSearch).toHaveBeenCalledWith('Ethereum')
    })

    it('should call onSearch when search button is clicked', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, 'Solana')
      
      const button = screen.getByTestId('search-button')
      await user.click(button)
      
      expect(mockOnSearch).toHaveBeenCalledWith('Solana')
    })

    it('should not search with empty query', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)
      
      const button = screen.getByTestId('search-button')
      await user.click(button)
      
      expect(mockOnSearch).not.toHaveBeenCalled()
    })

    it('should not search with whitespace only', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, '   ')
      
      const button = screen.getByTestId('search-button')
      await user.click(button)
      
      expect(mockOnSearch).not.toHaveBeenCalled()
    })

    it('should not search when disabled', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} disabled={true} />)
      
      const input = screen.getByTestId('search-input')
      // Note: Disabled input can't be typed in userEvent, so we simulate the value change
      fireEvent.change(input, { target: { value: 'Bitcoin' } })
      
      const form = screen.getByTestId('search-form')
      fireEvent.submit(form)
      
      expect(mockOnSearch).not.toHaveBeenCalled()
    })
  })

  describe('Suggestion interaction', () => {
    it('should call onSearch when suggestion is clicked', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)

      const input = screen.getByTestId('search-input')
      await user.type(input, 'BTC')

      await waitFor(() => {
        expect(screen.getByTestId('suggestion-0')).toBeInTheDocument()
      }, { timeout: 3000 })

      const suggestion = screen.getByTestId('suggestion-0')
      await user.click(suggestion)

      expect(mockOnSearch).toHaveBeenCalledWith('BTC price analysis')
      expect(input).toHaveValue('BTC price analysis')
    })

    it('should clear suggestions after clicking one', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)

      const input = screen.getByTestId('search-input')
      await user.type(input, 'BTC')

      await waitFor(() => {
        expect(screen.getByTestId('search-suggestions')).toBeInTheDocument()
      }, { timeout: 3000 })

      const suggestion = screen.getByTestId('suggestion-0')
      await user.click(suggestion)

      expect(screen.queryByTestId('search-suggestions')).not.toBeInTheDocument()
    })
  })

  describe('Button states', () => {
    it('should disable search button when input is empty', () => {
      render(<SearchBar onSearch={mockOnSearch} />)
      
      const button = screen.getByTestId('search-button')
      expect(button).toBeDisabled()
    })

    it('should enable search button when input has text', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={mockOnSearch} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, 'Bitcoin')
      
      const button = screen.getByTestId('search-button')
      expect(button).not.toBeDisabled()
    })

    it('should disable search button when component is disabled', () => {
      render(<SearchBar onSearch={mockOnSearch} disabled={true} />)
      
      const button = screen.getByTestId('search-button')
      expect(button).toBeDisabled()
    })
  })
})
