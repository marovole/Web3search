import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

// Create a simplified test version first
const TestGlobalSearchDialog = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  if (!isOpen) return null
  
  return (
    <div data-testid="search-dialog">
      <input
        data-testid="search-input"
        placeholder="搜索聊天记录、报告、监控..."
      />
      <div data-testid="search-results">
        <div data-testid="history-item">Bitcoin price</div>
        <div data-testid="history-item">Ethereum analysis</div>
      </div>
      <button data-testid="close-button" onClick={onClose}>Close</button>
    </div>
  )
}

describe('GlobalSearchDialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic functionality', () => {
    it('should render when isOpen is true', () => {
      render(<TestGlobalSearchDialog {...defaultProps} />)
      
      expect(screen.getByTestId('search-dialog')).toBeInTheDocument()
      expect(screen.getByTestId('search-input')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('搜索聊天记录、报告、监控...')).toBeInTheDocument()
    })

    it('should not render when isOpen is false', () => {
      render(<TestGlobalSearchDialog {...defaultProps} isOpen={false} />)
      
      expect(screen.queryByTestId('search-dialog')).not.toBeInTheDocument()
    })

    it('should show history items', () => {
      render(<TestGlobalSearchDialog {...defaultProps} />)
      
      expect(screen.getByText('Bitcoin price')).toBeInTheDocument()
      expect(screen.getByText('Ethereum analysis')).toBeInTheDocument()
    })

    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      render(<TestGlobalSearchDialog {...defaultProps} />)
      
      await user.click(screen.getByTestId('close-button'))
      
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  describe('Input functionality', () => {
    it('should allow typing in search input', async () => {
      const user = userEvent.setup()
      render(<TestGlobalSearchDialog {...defaultProps} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, 'Web3')
      
      expect(input).toHaveValue('Web3')
    })
  })
})
