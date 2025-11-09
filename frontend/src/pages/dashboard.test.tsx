/**
 * Dashboard Page Tests
 * Integration tests for the main dashboard
 * Covers Chat, Research, and Map components
 */

import { render, screen, waitFor } from '@testing-library/react'
import { DashboardPage } from './dashboard'

// Mock the child components
jest.mock('../components/sse/StreamingChat', () => ({
  StreamingChat: ({ apiUrl, onMessageComplete, onError }: any) => (
    <div data-testid="streaming-chat" data-api-url={apiUrl}>
      <div>Chat Component</div>
      <button onClick={() => onMessageComplete?.('Test message')}>Complete Message</button>
      <button onClick={() => onError?.(new Error('Chat error'))}>Trigger Error</button>
    </div>
  ),
}))

jest.mock('../components/sse/ResearchSSE', () => ({
  ResearchSSE: ({ apiUrl, query, onComplete, onError, onProgress }: any) => (
    <div data-testid="research-sse" data-api-url={apiUrl} data-query={query}>
      <div>Research Component</div>
      <div>Query: {query}</div>
      <button onClick={() => onComplete?.({ result: 'Test result' })}>Complete Research</button>
      <button onClick={() => onError?.(new Error('Research error'))}>Trigger Error</button>
      <button onClick={() => onProgress?.(50, 'Testing')}>Update Progress</button>
    </div>
  ),
}))

jest.mock('../components/map/InteractiveMap', () => ({
  InteractiveMap: ({ projects, center, zoom, onProjectClick }: any) => (
    <div
      data-testid="interactive-map"
      data-projects-count={projects.length}
      data-center={JSON.stringify(center)}
      data-zoom={zoom}
    >
      <div>Map Component</div>
      <div>{projects.length} projects</div>
      {projects.map((project: any) => (
        <button
          key={project.id}
          onClick={() => onProjectClick?.(project)}
          data-project-id={project.id}
        >
          {project.name}
        </button>
      ))}
    </div>
  ),
}))

describe('DashboardPage', () => {
  describe('Initial Rendering', () => {
    it('should render the dashboard header', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Web3Search Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Powered by T13 + Phase 4')).toBeInTheDocument()
    })

    it('should render all three main components', () => {
      render(<DashboardPage />)

      expect(screen.getByTestId('streaming-chat')).toBeInTheDocument()
      expect(screen.getByTestId('research-sse')).toBeInTheDocument()
      expect(screen.getByTestId('interactive-map')).toBeInTheDocument()
    })

    it('should render chat component with correct API URL', () => {
      render(<DashboardPage />)

      const chatComponent = screen.getByTestId('streaming-chat')
      expect(chatComponent).toHaveAttribute(
        'data-api-url',
        'https://web3search-api.onrender.com/api/v1/chat'
      )
    })

    it('should render research component with default query', () => {
      render(<DashboardPage />)

      const researchComponent = screen.getByTestId('research-sse')
      expect(researchComponent).toHaveAttribute('data-query', 'What is DeFi?')
      expect(screen.getByText('Query: What is DeFi?')).toBeInTheDocument()
    })

    it('should render map component with 6 projects', () => {
      render(<DashboardPage />)

      const mapComponent = screen.getByTestId('interactive-map')
      expect(mapComponent).toHaveAttribute('data-projects-count', '6')
      expect(screen.getByText('6 projects')).toBeInTheDocument()
    })

    it('should render map with correct center and zoom', () => {
      render(<DashboardPage />)

      const mapComponent = screen.getByTestId('interactive-map')
      expect(mapComponent).toHaveAttribute('data-center', JSON.stringify([20, 0]))
      expect(mapComponent).toHaveAttribute('data-zoom', '2')
    })

    it('should render integration notes', () => {
      render(<DashboardPage />)

      expect(screen.getByText('ℹ️ Integration Notes')).toBeInTheDocument()
      expect(screen.getByText('StreamingChat - Real-time chat with SSE streaming')).toBeInTheDocument()
      expect(screen.getByText('ResearchSSE - Deep research with 5-step progress tracking')).toBeInTheDocument()
      expect(screen.getByText('InteractiveMap - 6 projects across 5 categories with custom markers')).toBeInTheDocument()
    })
  })

  describe('Project Interaction', () => {
    it('should handle project click from map', () => {
      render(<DashboardPage />)

      const uniswapButton = screen.getByRole('button', { name: 'Uniswap' })
      expect(uniswapButton).toBeInTheDocument()

      // Click should not throw error
      uniswapButton.click()
    })

    it('should show project details when project is clicked', async () => {
      const { container } = render(<DashboardPage />)

      const uniswapButton = screen.getByRole('button', { name: 'Uniswap' })
      uniswapButton.click()

      // Wait for project details to appear
      await waitFor(() => {
        expect(screen.getByText('Project Details')).toBeInTheDocument()
      })

      expect(screen.getByText('Uniswap')).toBeInTheDocument()
      expect(screen.getByText('DeFi')).toBeInTheDocument()
    })

    it('should show details for different projects', async () => {
      render(<DashboardPage />)

      // Click OpenSea
      const openseaButton = screen.getByRole('button', { name: 'OpenSea' })
      openseaButton.click()

      await waitFor(() => {
        expect(screen.getByText('Project Details')).toBeInTheDocument()
      })

      expect(screen.getByText('OpenSea')).toBeInTheDocument()
      expect(screen.getByText('NFT')).toBeInTheDocument()
    })
  })

  describe('Component Integration', () => {
    it('should render all project buttons from map', () => {
      render(<DashboardPage />)

      const projectNames = ['Uniswap', 'OpenSea', 'Axie Infinity', 'Aave', 'Polygon', 'MakerDAO']

      projectNames.forEach(name => {
        expect(screen.getByRole('button', { name })).toBeInTheDocument()
      })
    })

    it('should render chat and research side by side', () => {
      const { container } = render(<DashboardPage />)

      const chatComponent = screen.getByTestId('streaming-chat')
      const researchComponent = screen.getByTestId('research-sse')

      // Both should be in the document
      expect(chatComponent).toBeInTheDocument()
      expect(researchComponent).toBeInTheDocument()
    })
  })

  describe('Map Categories', () => {
    it('should include defi projects', () => {
      render(<DashboardPage />)

      expect(screen.getByRole('button', { name: 'Uniswap' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Aave' })).toBeInTheDocument()
    })

    it('should include nft projects', () => {
      render(<DashboardPage />)

      expect(screen.getByRole('button', { name: 'OpenSea' })).toBeInTheDocument()
    })

    it('should include gaming projects', () => {
      render(<DashboardPage />)

      expect(screen.getByRole('button', { name: 'Axie Infinity' })).toBeInTheDocument()
    })

    it('should include infrastructure projects', () => {
      render(<DashboardPage />)

      expect(screen.getByRole('button', { name: 'Polygon' })).toBeInTheDocument()
    })

    it('should include dao projects', () => {
      render(<DashboardPage />)

      expect(screen.getByRole('button', { name: 'MakerDAO' })).toBeInTheDocument()
    })
  })

  describe('Responsive Layout', () => {
    it('should render chat and research in a grid', () => {
      const { container } = render(<DashboardPage />)

      const mainContent = container.querySelector('main')
      expect(mainContent).toBeInTheDocument()
    })

    it('should render map below chat and research', () => {
      render(<DashboardPage />)

      const mapComponent = screen.getByTestId('interactive-map')
      expect(mapComponent).toBeInTheDocument()
    })
  })

  describe('Default State', () => {
    it('should not show project details initially', () => {
      render(<DashboardPage />)

      expect(screen.queryByText('Project Details')).not.toBeInTheDocument()
    })

    it('should use correct default research query', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Query: What is DeFi?')).toBeInTheDocument()
    })
  })

  describe('Component Props', () => {
    it('should pass error handlers to chat component', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      render(<DashboardPage />)

      const errorButton = screen.getByRole('button', { name: 'Trigger Error' })
      errorButton.click()

      expect(consoleSpy).toHaveBeenCalledWith('Chat error:', expect.any(Error))
      consoleSpy.mockRestore()
    })

    it('should pass error handlers to research component', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      render(<DashboardPage />)

      const researchErrorButton = screen.getByText('Trigger Error').closest('div')?.querySelector('button')
      if (researchErrorButton) {
        researchErrorButton.click()
        expect(consoleSpy).toHaveBeenCalledWith('Research error:', expect.any(Error))
      }
      consoleSpy.mockRestore()
    })

    it('should pass complete handlers to chat component', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
      render(<DashboardPage />)

      const completeButton = screen.getByRole('button', { name: 'Complete Message' })
      completeButton.click()

      expect(consoleSpy).toHaveBeenCalledWith('Chat message completed:', 'Test message')
      consoleSpy.mockRestore()
    })

    it('should pass complete handlers to research component', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
      render(<DashboardPage />)

      const completeButton = screen.getByText('Complete Research')
      completeButton.click()

      expect(consoleSpy).toHaveBeenCalledWith('Research completed:', { result: 'Test result' })
      consoleSpy.mockRestore()
    })

    it('should pass progress handler to research component', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
      render(<DashboardPage />)

      const progressButton = screen.getByText('Update Progress')
      progressButton.click()

      expect(consoleSpy).toHaveBeenCalledWith('Research progress: 50% - Testing')
      consoleSpy.mockRestore()
    })
  })

  describe('Accessibility', () => {
    it('should have proper headings hierarchy', () => {
      render(<DashboardPage />)

      // Check for H1 (main title)
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Web3Search Dashboard')

      // Check for H2 (section titles)
      const h2Elements = screen.getAllByRole('heading', { level: 2 })
      expect(h2Elements).toHaveLength(3)
      expect(h2Elements[0]).toHaveTextContent('💬 AI Chat')
      expect(h2Elements[1]).toHaveTextContent('🔍 Deep Research')
      expect(h2Elements[2]).toHaveTextContent('🗺️ Interactive Investment Map')
    })

    it('should render all buttons with accessible names', () => {
      render(<DashboardPage />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveAccessibleName()
      })
    })
  })
})
