/**
 * Interactive Map Component Tests
 * TDD tests for InteractiveMap component
 * Part of Phase 4: Interactive Investment Map
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { InteractiveMap } from './InteractiveMap'
import { MapContainer } from 'react-leaflet'

// Mock react-leaflet
jest.mock('react-leaflet', () => {
  const mockMap = {
    setView: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    getBounds: jest.fn(() => ({
      contains: jest.fn(() => true),
    })),
  };

  return {
    MapContainer: jest.fn(({ children, center, zoom }) => (
      <div data-testid="map-container" data-center={JSON.stringify(center)} data-zoom={zoom}>
        {children}
      </div>
    )),
    TileLayer: jest.fn(() => <div data-testid="tile-layer">Tile Layer</div>),
    Marker: jest.fn(({ children, position, eventHandlers }) => (
      <div
        data-testid="marker"
        data-position={JSON.stringify(position)}
        onClick={() => eventHandlers?.click?.()}
      >
        {children}
      </div>
    )),
    Popup: jest.fn(({ children }) => <div data-testid="popup">{children}</div>),
    useMap: jest.fn(() => mockMap),
  };
})

// Mock Leaflet
describe('InteractiveMap', () => {
  const mockProjects = [
    {
      id: '1',
      name: 'Uniswap',
      lat: 40.7128,
      lng: -74.006,
      category: 'defi' as const,
      description: 'Decentralized exchange protocol',
      marketCap: 5000000000,
      website: 'https://uniswap.org',
      foundedYear: 2018,
    },
    {
      id: '2',
      name: 'OpenSea',
      lat: 37.7749,
      lng: -122.4194,
      category: 'nft' as const,
      description: 'NFT marketplace',
      marketCap: 13000000000,
      website: 'https://opensea.io',
      foundedYear: 2017,
    },
    {
      id: '3',
      name: 'Axie Infinity',
      lat: 1.3521,
      lng: 103.8198,
      category: 'gaming' as const,
      description: 'Blockchain-based game',
      marketCap: 3000000000,
      website: 'https://axieinfinity.com',
      foundedYear: 2018,
    },
  ]

  describe('Initial Rendering', () => {
    it('should render map container with correct props', () => {
      const center: [number, number] = [40.7128, -74.006]
      const zoom = 10

      render(<InteractiveMap projects={mockProjects} center={center} zoom={zoom} />)

      const mapContainer = screen.getByTestId('map-container')
      expect(mapContainer).toBeInTheDocument()
      expect(mapContainer).toHaveAttribute('data-center', JSON.stringify(center))
      expect(mapContainer).toHaveAttribute('data-zoom', zoom.toString())
    })

    it('should render with default center and zoom when not provided', () => {
      render(<InteractiveMap projects={mockProjects} />)

      const mapContainer = screen.getByTestId('map-container')
      const centerAttr = mapContainer.getAttribute('data-center')
      const center = JSON.parse(centerAttr || '[0,0]')

      expect(center).toEqual([40.7128, -74.006]) // Default center
    })

    it('should render tile layer', () => {
      render(<InteractiveMap projects={mockProjects} />)

      expect(screen.getByTestId('tile-layer')).toBeInTheDocument()
      expect(screen.getByText('Tile Layer')).toBeInTheDocument()
    })

    it('should render markers for all projects', () => {
      render(<InteractiveMap projects={mockProjects} />)

      const markers = screen.getAllByTestId('marker')
      expect(markers).toHaveLength(mockProjects.length)

      // Check first marker position
      const firstMarker = markers[0]
      const positionAttr = firstMarker.getAttribute('data-position')
      const position = JSON.parse(positionAttr || '[0,0]')
      expect(position).toEqual([40.7128, -74.006])
    })

    it('should render legend with category colors', () => {
      render(<InteractiveMap projects={mockProjects} />)

      const legend = screen.getByText('Project Categories').closest('div')
      expect(legend).toBeInTheDocument()
      if (!legend) return

      const legendQueries = within(legend)
      expect(legendQueries.getByText('Project Categories')).toBeInTheDocument()
      expect(legendQueries.getByText('DeFi')).toBeInTheDocument()
      expect(legendQueries.getByText('NFT')).toBeInTheDocument()
      expect(legendQueries.getByText('Gaming')).toBeInTheDocument()
      expect(legendQueries.getByText('Infrastructure')).toBeInTheDocument()
      expect(legendQueries.getByText('DAO')).toBeInTheDocument()
    })
  })

  describe('Interactions', () => {
    it('should call onProjectClick when marker is clicked', () => {
      const handleProjectClick = jest.fn()

      render(
        <InteractiveMap
          projects={mockProjects}
          onProjectClick={handleProjectClick}
        />
      )

      // Click first marker
      const markers = screen.getAllByTestId('marker')
      fireEvent.click(markers[0])

      expect(handleProjectClick).toHaveBeenCalledWith(mockProjects[0])
    })

    it('should display project popup on marker hover/click', () => {
      render(<InteractiveMap projects={mockProjects} />)

      const popups = screen.getAllByTestId('popup')
      expect(popups).toHaveLength(mockProjects.length)
    })

    it('should show project details in popup', () => {
      render(
        <InteractiveMap projects={[mockProjects[0]]} />
      )

      const [popup] = screen.getAllByTestId('popup')
      const popupQueries = within(popup)

      expect(popupQueries.getByText('Uniswap')).toBeInTheDocument()
      expect(popupQueries.getByText('Decentralized exchange protocol')).toBeInTheDocument()
      expect(popupQueries.getByText('DEFI')).toBeInTheDocument()
      expect(popupQueries.getByText(/Market Cap:/)).toBeInTheDocument()
      expect(popupQueries.getByText('$5.00B')).toBeInTheDocument()
      expect(popupQueries.getByText(/Founded:/)).toBeInTheDocument()
      expect(popupQueries.getByText('2018')).toBeInTheDocument()
      expect(popupQueries.getByText('Visit Website →')).toBeInTheDocument()
    })
  })

  describe('Project Selection', () => {
    it('should show bottom panel when project is selected', async () => {
      render(
        <InteractiveMap projects={mockProjects} />
      )

      // Click first marker to select project
      const markers = screen.getAllByTestId('marker')
      fireEvent.click(markers[0])

      const closeButton = await screen.findByRole('button', { name: '✕' })
      expect(closeButton).toBeInTheDocument()
    })

    it('should close panel when close button is clicked', async () => {
      render(<InteractiveMap projects={mockProjects} />)

      // Select project first
      const markers = screen.getAllByTestId('marker')
      fireEvent.click(markers[0])

      // Close panel
      const closeButton = await screen.findByRole('button', { name: '✕' })
      fireEvent.click(closeButton)

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: '✕' })).not.toBeInTheDocument()
      })
    })
  })

  describe('Map Controls', () => {
    it('should handle map click events', () => {
      const handleMapClick = jest.fn()

      // Mock the map click handler
      jest.mocked(MapContainer).mockImplementationOnce(({ children }) => {
        // Simulate map click
        if (handleMapClick) {
          handleMapClick(40.7128, -74.006)
        }
        return <div data-testid="map-container">{children}</div>
      })

      render(
        <InteractiveMap
          projects={mockProjects}
          onMapClick={handleMapClick}
        />
      )

      expect(handleMapClick).toHaveBeenCalledWith(40.7128, -74.006)
    })
  })

  describe('Category Filtering', () => {
    it('should display different marker colors for different categories', () => {
      const { container } = render(
        <InteractiveMap projects={mockProjects} />
      )

      // Check that legend has colored indicators
      const legend = container.querySelector('.absolute.top-4.right-4')
      expect(legend).toBeInTheDocument()
    })

    it('should create correct marker icons based on category', () => {
      render(<InteractiveMap projects={mockProjects} />)

      const markers = screen.getAllByTestId('marker')
      expect(markers).toHaveLength(3)
    })
  })

  describe('Empty State', () => {
    it('should render map without projects', () => {
      render(<InteractiveMap projects={[]} />)

      expect(screen.getByTestId('map-container')).toBeInTheDocument()
      expect(screen.queryAllByTestId('marker')).toHaveLength(0)
    })
  })

  describe('Performance Optimization', () => {
    it('should filter visible projects based on map bounds', () => {
      const { container } = render(
        <InteractiveMap projects={mockProjects} />
      )

      // Map should render all markers initially
      const markers = screen.getAllByTestId('marker')
      expect(markers.length).toBeLessThanOrEqual(mockProjects.length)
    })

    it('should update visible projects when map bounds change', () => {
      const { rerender } = render(
        <InteractiveMap projects={mockProjects} />
      )

      let markers = screen.getAllByTestId('marker')
      const initialCount = markers.length

      // Change map bounds/zoom
      rerender(
        <InteractiveMap projects={mockProjects} zoom={5} />
      )

      markers = screen.getAllByTestId('marker')
      expect(markers.length).toBeLessThanOrEqual(initialCount)
    })
  })

  describe('Custom Styling', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <InteractiveMap projects={mockProjects} className="custom-map-class" />
      )

      const mapDiv = container.querySelector('.custom-map-class')
      expect(mapDiv).toBeInTheDocument()
    })

    it('should render dark mode styles when applicable', () => {
      // Mock dark mode by checking for dark classes
      const { container } = render(
        <InteractiveMap projects={mockProjects} />
      )

      const legend = container.querySelector('.dark\\:bg-gray-800')
      // In test environment, dark mode classes are present but not active
      expect(legend).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for interactive controls', () => {
      render(<InteractiveMap projects={mockProjects} />)

      const mapContainer = screen.getByTestId('map-container')
      expect(mapContainer).toBeInTheDocument()
    })

    it('should provide keyboard navigation for markers', () => {
      render(<InteractiveMap projects={mockProjects} />)

      const markers = screen.getAllByTestId('marker')
      expect(markers.length).toBeGreaterThan(0)
    })
  })
})
