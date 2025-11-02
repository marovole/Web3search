import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { GlobalSearchDialog } from '../../../components/Search/GlobalSearchDialog'

// Mock framer-motion (support any motion.* tag)
jest.mock('framer-motion', () => {
  const React = require('react')
  const Motion = new Proxy({}, {
    get: () => (props: any) => <div {...props} />,
  })
  return {
    motion: Motion,
    AnimatePresence: ({ children }: any) => <>{children}</>,
  }
})

// Mock lucide-react
jest.mock('lucide-react', () => ({
  Search: ({ className }: any) => <div data-testid="search-icon" className={className} />,
  Clock: ({ className }: any) => <div data-testid="clock-icon" className={className} />,
  ArrowRight: ({ className }: any) => <div data-testid="arrow-icon" className={className} />,
}))

// Mock react-router-dom
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

// Mock SearchHistoryContext
const mockGetRecentHistory = jest.fn()
jest.mock('../../../contexts/SearchHistoryContext', () => ({
  useSearchHistory: () => ({
    getRecentHistory: mockGetRecentHistory,
  }),
}))

// Mock utils
jest.mock('../../../lib/utils', () => ({
  cn: (...classes: any[]) => classes.filter(Boolean).join(' '),
}))

describe('GlobalSearchDialog Integration', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
    document.body.style.overflow = ''
    mockGetRecentHistory.mockReturnValue([
      { id: '1', query: 'Bitcoin price', timestamp: Date.now(), resultsCount: 10, type: 'chat' as const },
      { id: '2', query: 'Ethereum analysis', timestamp: Date.now() - 86400000, resultsCount: 5, type: 'report' as const },
    ])
  })

  afterEach(() => {
    document.body.style.overflow = ''
  })

  describe('Component rendering', () => {
    it('should render dialog with correct elements', () => {
      render(<GlobalSearchDialog {...defaultProps} />)
      
      expect(screen.getByTestId('search-input')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('搜索聊天记录、报告、监控...')).toBeInTheDocument()
      expect(screen.getAllByTestId('search-icon').length).toBeGreaterThan(0)
    })

    it('should show recent history when no query', async () => {
      render(<GlobalSearchDialog {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Bitcoin price')).toBeInTheDocument()
        expect(screen.getByText('Ethereum analysis')).toBeInTheDocument()
      })
      expect(screen.getAllByTestId('clock-icon').length).toBeGreaterThan(0)
    })

    it('should show empty state when no history', () => {
      mockGetRecentHistory.mockReturnValue([])
      render(<GlobalSearchDialog {...defaultProps} />)
      
      expect(screen.getByText('最近搜索')).toBeInTheDocument()
      expect(screen.getByText('暂无搜索历史')).toBeInTheDocument()
    })
  })

  describe('Search functionality', () => {
    it('should filter suggestions based on query', async () => {
      const user = userEvent.setup()
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, 'Web3')
      
      await waitFor(() => {
        expect(screen.getByText('Web3技术趋势')).toBeInTheDocument()
      })
      
      expect(screen.queryByText('Bitcoin price')).not.toBeInTheDocument()
      expect(screen.getAllByTestId('search-icon').length).toBeGreaterThan(0)
    })

    it('should show no results when query has no matches', async () => {
      const user = userEvent.setup()
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, 'xyz123')
      
      await waitFor(() => {
        expect(screen.getByText('未找到相关结果')).toBeInTheDocument()
      })
    })

    it('should navigate on Enter with query', async () => {
      const user = userEvent.setup()
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const input = screen.getByTestId('search-input') as HTMLInputElement
      fireEvent.change(input, { target: { value: 'Bitcoin' } })
      fireEvent.keyDown(document, { key: 'Enter' })
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/search?q=Bitcoin')
        expect(defaultProps.onClose).toHaveBeenCalled()
      })
    })

    it('should not search with empty query', async () => {
      const user = userEvent.setup()
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const input = screen.getByTestId('search-input')
      await user.type(input, '{enter}')
      
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  describe('History interaction', () => {
    it('should navigate when clicking history item', async () => {
      const user = userEvent.setup()
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const historyItem = screen.getByText('Bitcoin price')
      await user.click(historyItem)
      
      expect(mockNavigate).toHaveBeenCalledWith('/search?q=Bitcoin%20price')
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  describe('Keyboard navigation', () => {
    it('should close dialog with Escape key', () => {
      render(<GlobalSearchDialog {...defaultProps} />)
      
      fireEvent.keyDown(document, { key: 'Escape' })
      
      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should focus input when opened', () => {
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const input = screen.getByTestId('search-input')
      expect(input).toHaveFocus()
    })

    it('should navigate items with ArrowDown and ArrowUp without errors', async () => {
      const user = userEvent.setup()
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const input = screen.getByTestId('search-input')
      fireEvent.change(input, { target: { value: 'Web3' } })
      
      await waitFor(() => {
        expect(screen.getByText('Web3技术趋势')).toBeInTheDocument()
      })
      
      // Arrow navigation should not throw errors
      expect(() => {
        fireEvent.keyDown(document, { key: 'ArrowDown' })
        fireEvent.keyDown(document, { key: 'ArrowDown' })
        fireEvent.keyDown(document, { key: 'ArrowUp' })
      }).not.toThrow()
    })

    it('should select item with Enter when highlighted', async () => {
      const user = userEvent.setup()
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const input = screen.getByTestId('search-input')
      fireEvent.change(input, { target: { value: 'Web3' } })
      
      await waitFor(() => {
        expect(screen.getByText('Web3技术趋势')).toBeInTheDocument()
      })
      
      // Select first item
      fireEvent.keyDown(document, { key: 'ArrowDown' })
      fireEvent.keyDown(document, { key: 'Enter' })
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/search?q=Web3%E6%8A%80%E6%9C%AF%E8%B6%8B%E5%8A%BF')
        expect(defaultProps.onClose).toHaveBeenCalled()
      })
    })
  })

  describe('Accessibility and behavior', () => {
    it('should close when clicking backdrop', () => {
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const backdrop = screen.getByPlaceholderText('搜索聊天记录、报告、监控...').closest('div')?.parentElement?.parentElement?.previousElementSibling
      if (backdrop) {
        fireEvent.click(backdrop)
        expect(defaultProps.onClose).toHaveBeenCalled()
      }
    })

    it('should not close when clicking dialog content', () => {
      render(<GlobalSearchDialog {...defaultProps} />)
      
      const dialog = screen.getByPlaceholderText('搜索聊天记录、报告、监控...').closest('div')?.parentElement?.parentElement
      if (dialog) {
        fireEvent.click(dialog)
        expect(defaultProps.onClose).not.toHaveBeenCalled()
      }
    })

    it('should prevent body scroll when open', () => {
      render(<GlobalSearchDialog {...defaultProps} />)
      
      expect(document.body.style.overflow).toBe('hidden')
    })

    it('should restore body scroll when closed', () => {
      const { rerender } = render(<GlobalSearchDialog {...defaultProps} />)
      
      rerender(<GlobalSearchDialog {...defaultProps} isOpen={false} />)
      
      expect(document.body.style.overflow).toBe('')
    })
  })
})
