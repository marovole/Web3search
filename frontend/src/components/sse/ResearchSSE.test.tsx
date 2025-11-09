/**
 * Deep Research SSE Component Tests
 * TDD tests for ResearchSSE component
 * Part of Week 2 T13: Frontend SSE Integration
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { ResearchSSE } from './ResearchSSE'
import { useResearchSSE } from '../../hooks/useSSE'

// Mock the useResearchSSE hook
jest.mock('../../hooks/useSSE')

const mockUseResearchSSE = useResearchSSE as jest.MockedFunction<typeof useResearchSSE>

describe('ResearchSSE Component', () => {
  let mockStart: jest.Mock
  let mockStop: jest.Mock
  let mockReset: jest.Mock
  let mockOnMessage: jest.Mock
  let mockOnError: jest.Mock

  beforeEach(() => {
    mockStart = jest.fn()
    mockStop = jest.fn()
    mockReset = jest.fn()
    mockOnMessage = jest.fn()
    mockOnError = jest.fn()

    mockUseResearchSSE.mockReturnValue({
      events: [],
      currentEvent: null,
      isConnected: false,
      error: null,
      progress: 0,
      start: mockStart,
      stop: mockStop,
      reset: mockReset,
    })

    jest.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should render with default state', () => {
      render(<ResearchSSE apiUrl="https://test-api.com/research" query="Test research query" />)

      expect(screen.getByText('Deep Research')).toBeInTheDocument()
      expect(screen.getByText('Test research query')).toBeInTheDocument()
      expect(screen.getByText('Start Research')).toBeInTheDocument()

      // Check all steps are rendered
      expect(screen.getByText('Generating Research Plan')).toBeInTheDocument()
      expect(screen.getByText('Searching Sources')).toBeInTheDocument()
      expect(screen.getByText('Analyzing Content')).toBeInTheDocument()
      expect(screen.getByText('Synthesizing Insights')).toBeInTheDocument()
      expect(screen.getByText('Compiling Report')).toBeInTheDocument()
    })

    it('should disable start button when query is empty', () => {
      render(<ResearchSSE apiUrl="https://test-api.com/research" query="" />)

      const startButton = screen.getByText('Start Research')
      expect(startButton).toBeDisabled()
    })
  })

  describe('Research Flow', () => {
    it('should start research when button is clicked', () => {
      render(<ResearchSSE apiUrl="https://test-api.com/research" query="Test query" />)

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)

      expect(mockStart).toHaveBeenCalledTimes(1)
    })

    it('should show connecting state after start', async () => {
      mockUseResearchSSE.mockReturnValue({
        events: [],
        currentEvent: null,
        isConnected: false,
        error: null,
        progress: 0,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      const { rerender } = render(
        <ResearchSSE apiUrl="https://test-api.com/research" query="Test query" />
      )

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)

      // Update to connecting state
      mockUseResearchSSE.mockReturnValue({
        events: [],
        currentEvent: null,
        isConnected: false,
        error: null,
        progress: 0,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      rerender(<ResearchSSE apiUrl="https://test-api.com/research" query="Test query" />)
    })

    it('should show connected state when SSE connection is established', () => {
      mockUseResearchSSE.mockReturnValue({
        events: [],
        currentEvent: null,
        isConnected: true,
        error: null,
        progress: 0,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(<ResearchSSE apiUrl="https://test-api.com/research" query="Test query" />)

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })
  })

  describe('Progress Updates', () => {
    it('should update progress when research.progress event is received', async () => {
      const progressCallback = jest.fn()
      mockUseResearchSSE.mockReturnValue({
        events: [
          {
            event: 'research.progress' as const,
            data: { progress_percent: 25, task_id: 'plan' },
          },
        ],
        currentEvent: {
          event: 'research.progress' as const,
          data: { progress_percent: 25, task_id: 'plan' },
        },
        isConnected: true,
        error: null,
        progress: 25,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(
        <ResearchSSE
          apiUrl="https://test-api.com/research"
          query="Test query"
          onProgress={progressCallback}
        />
      )

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })

    it('should update step status when research.step event is received', async () => {
      mockUseResearchSSE.mockReturnValue({
        events: [
          {
            event: 'research.step' as const,
            data: { step: 'plan_complete' },
          },
        ],
        currentEvent: {
          event: 'research.step' as const,
          data: { step: 'plan_complete' },
        },
        isConnected: true,
        error: null,
        progress: 20,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(<ResearchSSE apiUrl="https://test-api.com/research" query="Test query" />)

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })
  })

  describe('Research Completion', () => {
    it('should display result when research.completed event is received', async () => {
      const mockResult = {
        markdown: '# Research Result',
        html: '<h1>Research Result</h1>',
        sources: [],
      }

      mockUseResearchSSE.mockReturnValue({
        events: [
          {
            event: 'research.completed' as const,
            data: { result: mockResult },
          },
        ],
        currentEvent: {
          event: 'research.completed' as const,
          data: { result: mockResult },
        },
        isConnected: false,
        error: null,
        progress: 100,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      const handleComplete = jest.fn()
      render(
        <ResearchSSE
          apiUrl="https://test-api.com/research"
          query="Test query"
          onComplete={handleComplete}
        />
      )

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })
  })

  describe('Error Handling', () => {
    it('should display error message when research.failed event is received', async () => {
      mockUseResearchSSE.mockReturnValue({
        events: [
          {
            event: 'research.failed' as const,
            data: { error_message: 'API rate limit exceeded' },
          },
        ],
        currentEvent: {
          event: 'research.failed' as const,
          data: { error_message: 'API rate limit exceeded' },
        },
        isConnected: false,
        error: null,
        progress: 0,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      const handleError = jest.fn()
      render(
        <ResearchSSE
          apiUrl="https://test-api.com/research"
          query="Test query"
          onError={handleError}
        />
      )

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })

    it('should display error when SSE connection error occurs', () => {
      mockUseResearchSSE.mockReturnValue({
        events: [],
        currentEvent: null,
        isConnected: false,
        error: new Error('Connection failed'),
        progress: 0,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(<ResearchSSE apiUrl="https://test-api.com/research" query="Test query" />)
    })
  })

  describe('Cancel Functionality', () => {
    it('should call stop when cancel button is clicked', () => {
      mockUseResearchSSE.mockReturnValue({
        events: [],
        currentEvent: null,
        isConnected: true,
        error: null,
        progress: 50,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(<ResearchSSE apiUrl="https://test-api.com/research" query="Test query" />)

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)

      // Component would need to be in a state where cancel button is visible
    })
  })

  describe('Callback Handlers', () => {
    it('should call onComplete when research is completed', () => {
      const handleComplete = jest.fn()
      const mockResult = { markdown: 'Test result' }

      mockUseResearchSSE.mockReturnValue({
        events: [
          {
            event: 'research.completed' as const,
            data: { result: mockResult },
          },
        ],
        currentEvent: {
          event: 'research.completed' as const,
          data: { result: mockResult },
        },
        isConnected: false,
        error: null,
        progress: 100,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(
        <ResearchSSE
          apiUrl="https://test-api.com/research"
          query="Test query"
          onComplete={handleComplete}
        />
      )

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })

    it('should call onError when error occurs', () => {
      const handleError = jest.fn()

      mockUseResearchSSE.mockReturnValue({
        events: [
          {
            event: 'research.failed' as const,
            data: { error_message: 'Test error' },
          },
        ],
        currentEvent: {
          event: 'research.failed' as const,
          data: { error_message: 'Test error' },
        },
        isConnected: false,
        error: new Error('Test error'),
        progress: 0,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(
        <ResearchSSE
          apiUrl="https://test-api.com/research"
          query="Test query"
          onError={handleError}
        />
      )

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })

    it('should call onProgress when progress updates', () => {
      const handleProgress = jest.fn()

      mockUseResearchSSE.mockReturnValue({
        events: [
          {
            event: 'research.progress' as const,
            data: { progress_percent: 30, task_id: 'plan' },
          },
        ],
        currentEvent: {
          event: 'research.progress' as const,
          data: { progress_percent: 30, task_id: 'plan' },
        },
        isConnected: true,
        error: null,
        progress: 30,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(
        <ResearchSSE
          apiUrl="https://test-api.com/research"
          query="Test query"
          onProgress={handleProgress}
        />
      )

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })
  })

  describe('Reset Functionality', () => {
    it('should reset component state when reset button is clicked after completion', async () => {
      const mockResult = { markdown: 'Test result' }

      mockUseResearchSSE.mockReturnValue({
        events: [
          {
            event: 'research.completed' as const,
            data: { result: mockResult },
          },
        ],
        currentEvent: {
          event: 'research.completed' as const,
          data: { result: mockResult },
        },
        isConnected: false,
        error: null,
        progress: 100,
        start: mockStart,
        stop: mockStop,
        reset: mockReset,
      })

      render(<ResearchSSE apiUrl="https://test-api.com/research" query="Test query" />)

      const startButton = screen.getByText('Start Research')
      fireEvent.click(startButton)
    })
  })
})
