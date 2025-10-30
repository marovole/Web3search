import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ModeSwitch from './ModeSwitch'

describe('ModeSwitch component', () => {
  const mockOnChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should render both modes', () => {
    render(<ModeSwitch mode="quick" onChange={mockOnChange} />)
    
    expect(screen.getByText(/Quick Chat|快速/)).toBeInTheDocument()
    expect(screen.getByText(/Deep Research|深度/)).toBeInTheDocument()
  })

  it('should call onChange when switching to deep mode', async () => {
    render(<ModeSwitch mode="quick" onChange={mockOnChange} />)
    
    const deepButton = screen.getByText(/Deep Research|深度/)
    fireEvent.click(deepButton)

    await vi.runAllTimersAsync()

    expect(mockOnChange).toHaveBeenCalledWith('deep')
  })

  it('should call onChange when switching to quick mode', async () => {
    render(<ModeSwitch mode="deep" onChange={mockOnChange} />)
    
    const quickButton = screen.getAllByText(/Quick Chat|快速/)[0]
    fireEvent.click(quickButton)

    await vi.runAllTimersAsync()

    expect(mockOnChange).toHaveBeenCalledWith('quick')
  })

  it('should not call onChange when clicking current mode', () => {
    render(<ModeSwitch mode="quick" onChange={mockOnChange} />)
    
    const quickButton = screen.getAllByText(/Quick Chat|快速/)[0]
    fireEvent.click(quickButton)

    expect(mockOnChange).not.toHaveBeenCalled()
  })

  it('should display mode description', () => {
    render(<ModeSwitch mode="quick" onChange={mockOnChange} />)
    
    expect(screen.getByText(/3秒快速回答/)).toBeInTheDocument()
    
    const { rerender } = render(<ModeSwitch mode="deep" onChange={mockOnChange} />)
    expect(screen.getByText(/30秒深度报告/)).toBeInTheDocument()
  })
})

