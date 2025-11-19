/**
 * Dashboard Page
 * Main application dashboard with chat, research, and map
 * Part of T13 + Phase 4 Integration
 */

import { useState } from 'react'
import { StreamingChat } from '../components/sse/StreamingChat'
import { ResearchSSE } from '../components/sse/ResearchSSE'
import { InteractiveMap } from '../components/map/InteractiveMap'

// Mock data for the map
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
    logo: 'https://cryptologos.cc/logos/uniswap-uni-logo.png',
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
    logo: 'https://cryptologos.cc/logos/opensea-logo.png',
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
    logo: 'https://cryptologos.cc/logos/axie-infinity-axs-logo.png',
  },
  {
    id: '4',
    name: 'Aave',
    lat: 51.5074,
    lng: -0.1278,
    category: 'defi' as const,
    description: 'Decentralized lending protocol',
    marketCap: 2000000000,
    website: 'https://aave.com',
    foundedYear: 2017,
    logo: 'https://cryptologos.cc/logos/aave-aave-logo.png',
  },
  {
    id: '5',
    name: 'Polygon',
    lat: 19.076,
    lng: 72.8777,
    category: 'infrastructure' as const,
    description: 'Ethereum scaling solution',
    marketCap: 8000000000,
    website: 'https://polygon.technology',
    foundedYear: 2017,
    logo: 'https://cryptologos.cc/logos/polygon-matic-logo.png',
  },
  {
    id: '6',
    name: 'MakerDAO',
    lat: 52.52,
    lng: 13.405,
    category: 'dao' as const,
    description: 'Decentralized autonomous organization',
    marketCap: 1500000000,
    website: 'https://makerdao.com',
    foundedYear: 2017,
    logo: 'https://cryptologos.cc/logos/maker-mkr-logo.png',
  },
]

export function DashboardPage() {
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [researchQuery, setResearchQuery] = useState<string>('What is DeFi?')

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Web3Search Dashboard
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Powered by T13 + Phase 4
              </span>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Chat */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                💬 AI Chat
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Real-time chat with streaming responses
              </p>
            </div>
            <div className="h-96">
              <StreamingChat
                apiUrl={`${import.meta.env.VITE_API_BASE_URL || 'https://api.lulaai.xyz'}/api/v1/chat/quick-chat`}
                onMessageComplete={(message) => {
                  console.log('Chat message completed:', message)
                }}
                onError={(error) => {
                  console.error('Chat error:', error)
                }}
              />
            </div>
          </div>

          {/* Right Column - Deep Research */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                🔍 Deep Research
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Comprehensive research with real-time progress
              </p>
            </div>
            <div className="p-6">
              <ResearchSSE
                apiUrl={`${import.meta.env.VITE_API_BASE_URL || 'https://api.lulaai.xyz'}/api/v1/chat/deep-research/stream`}
                query={researchQuery}
                onComplete={(result) => {
                  console.log('Research completed:', result)
                }}
                onError={(error) => {
                  console.error('Research error:', error)
                }}
                onProgress={(progress, step) => {
                  console.log(`Research progress: ${progress}% - ${step}`)
                }}
              />
            </div>
          </div>
        </div>

        {/* Full Width Map */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              🗺️ Interactive Investment Map
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Explore crypto projects by location and category
            </p>
          </div>
          <div className="h-96">
            <InteractiveMap
              projects={mockProjects}
              center={[20, 0]}
              zoom={2}
              onProjectClick={(project) => {
                setSelectedProject(project.id)
                console.log('Selected project:', project)
              }}
            />
          </div>
        </div>

        {/* Selected Project Details */}
        {selectedProject && (
          <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Project Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Selected Project
                </p>
                <p className="text-gray-900 dark:text-white">
                  {mockProjects.find(p => p.id === selectedProject)?.name}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Category
                </p>
                <p className="text-gray-900 dark:text-white">
                  {mockProjects.find(p => p.id === selectedProject)?.category.toUpperCase()}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Integration Notes */}
        <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-2">
            ℹ️ Integration Notes
          </h3>
          <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-400">
            <li className="flex items-start">
              <span className="mr-2">✅</span>
              <span>StreamingChat - Real-time chat with SSE streaming</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">✅</span>
              <span>ResearchSSE - Deep research with 5-step progress tracking</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">✅</span>
              <span>InteractiveMap - 6 projects across 5 categories with custom markers</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">⏳</span>
              <span>Connect to real API endpoints after testing</span>
            </li>
          </ul>
        </div>
      </main>
    </div>
  )
}

export default DashboardPage
