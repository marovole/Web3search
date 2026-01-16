import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import WatchlistPage from '../../pages/WatchlistPage'

const mockNavigate = jest.fn()
const mockAddToWatchlist = jest.fn()
const mockRemoveFromWatchlist = jest.fn()
const mockClearWatchlist = jest.fn()

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: true, session: { access_token: 'token' } }),
}))

jest.mock('../../hooks/useApiWatchlist', () => ({
  useApiWatchlist: () => ({
    watchlist: [
      { id: 'watch-1', symbol: 'BTC', name: 'Bitcoin', coingecko_id: 'bitcoin' }
    ],
    loading: false,
    error: null,
    addToWatchlist: mockAddToWatchlist,
    removeFromWatchlist: mockRemoveFromWatchlist,
    clearWatchlist: mockClearWatchlist,
  })
}))

jest.mock('../../components/Watchlist/TokenSearchInput', () => ({
  __esModule: true,
  default: ({ onSelect }: { onSelect: (token: { id: string; symbol: string; name: string; thumb: string }) => void }) => (
    <button type="button" onClick={() => onSelect({ id: 'ethereum', symbol: 'eth', name: 'Ethereum', thumb: '' })}>
      add token
    </button>
  )
}))

jest.mock('../../components/Watchlist/WatchlistCard', () => ({
  __esModule: true,
  default: ({ id, symbol, onRemove }: { id: string; symbol: string; onRemove: (id: string) => void }) => (
    <div>
      <span>{symbol}</span>
      <button type="button" onClick={() => onRemove(id)}>remove</button>
    </div>
  )
}))

jest.mock('../../services/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn().mockResolvedValue({ data: { prices: {} } }),
  },
}))

describe('WatchlistPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockAddToWatchlist.mockResolvedValue(true)
  })

  it('renders watchlist items', () => {
    render(<WatchlistPage />)

    expect(screen.getByText('BTC')).toBeInTheDocument()
  })

  it('adds token via search input', async () => {
    render(<WatchlistPage />)

    fireEvent.click(screen.getByRole('button', { name: /add token/i }))

    await waitFor(() => {
      expect(mockAddToWatchlist).toHaveBeenCalledWith({
        token_id: 'ethereum',
        symbol: 'ETH',
        name: 'Ethereum',
        coingecko_id: 'ethereum',
        logo_url: ''
      })
    })
  })

  it('removes token from watchlist', async () => {
    render(<WatchlistPage />)

    fireEvent.click(screen.getByRole('button', { name: /remove/i }))

    await waitFor(() => {
      expect(mockRemoveFromWatchlist).toHaveBeenCalledWith('watch-1')
    })
  })

  it('clears watchlist after confirmation', async () => {
    render(<WatchlistPage />)

    const clearButton = screen.getByRole('button', { name: /clear all/i })
    fireEvent.click(clearButton)

    const confirmButton = screen.getByRole('button', { name: /confirm clear/i })
    fireEvent.click(confirmButton)

    await waitFor(() => {
      expect(mockClearWatchlist).toHaveBeenCalled()
    })
  })
})
