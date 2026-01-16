import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import HoldingsPage from '../../pages/HoldingsPage'

const mockDeleteHolding = jest.fn()
const mockRefresh = jest.fn()
const mockFetchDiagnosis = jest.fn()

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: true }),
}))

jest.mock('../../hooks/useHoldings', () => ({
  useHoldings: () => ({
    holdings: [
      {
        id: 'hold-1',
        symbol: 'BTC',
        name: 'Bitcoin',
        quantity: 1,
        avg_buy_price: 40000,
        price_usd: 45000,
      },
    ],
    summary: { total_value_usd: 45000 },
    loading: false,
    deleteHolding: mockDeleteHolding,
    refresh: mockRefresh,
  })
}))

jest.mock('../../hooks/useDiagnosis', () => ({
  useDiagnosis: () => ({
    latestDiagnosis: null,
    loading: false,
    fetchLatest: mockFetchDiagnosis,
  })
}))

jest.mock('../../components/Holdings', () => ({
  AddHoldingModal: () => <div data-testid="add-holding-modal" />,
  DiagnosisReport: () => <div data-testid="diagnosis-report" />,
}))

describe('HoldingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    Object.defineProperty(window, 'confirm', {
      value: jest.fn(() => true),
      writable: true,
    })
  })

  it('renders holdings and deletes a holding', async () => {
    render(<HoldingsPage />)

    fireEvent.click(screen.getByRole('button', { name: /删除/i }))

    await waitFor(() => {
      expect(mockDeleteHolding).toHaveBeenCalledWith('hold-1')
    })
  })

  it('fetches diagnosis when switching to diagnosis tab', async () => {
    render(<HoldingsPage />)

    fireEvent.click(screen.getByRole('button', { name: /诊断/i }))

    await waitFor(() => {
      expect(mockFetchDiagnosis).toHaveBeenCalled()
    })
  })
})
