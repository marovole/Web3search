import React, { useState, useEffect, useRef, useCallback } from 'react'

// Types
export interface TokenSearchResult {
  id: string
  symbol: string
  name: string
  thumb: string
  market_cap_rank: number | null
}

interface TokenSearchInputProps {
  onSelect: (token: TokenSearchResult) => void
  placeholder?: string
  disabled?: boolean
}

// Mock API function to simulate CoinGecko search
// In a real implementation, this would call the backend API
const mockSearchTokens = async (query: string): Promise<TokenSearchResult[]> => {
  await new Promise(resolve => setTimeout(resolve, 500)) // Simulate network delay
  
  const queryLower = query.toLowerCase()
  
  // Mock database
  const mockTokens: TokenSearchResult[] = [
    { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', thumb: 'https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png', market_cap_rank: 1 },
    { id: 'ethereum', symbol: 'ETH', name: 'Ethereum', thumb: 'https://assets.coingecko.com/coins/images/279/thumb/ethereum.png', market_cap_rank: 2 },
    { id: 'tether', symbol: 'USDT', name: 'Tether', thumb: 'https://assets.coingecko.com/coins/images/325/thumb/Tether.png', market_cap_rank: 3 },
    { id: 'binancecoin', symbol: 'BNB', name: 'BNB', thumb: 'https://assets.coingecko.com/coins/images/825/thumb/bnb-icon2_2x.png', market_cap_rank: 4 },
    { id: 'solana', symbol: 'SOL', name: 'Solana', thumb: 'https://assets.coingecko.com/coins/images/4128/thumb/solana.png', market_cap_rank: 5 },
    { id: 'ripple', symbol: 'XRP', name: 'XRP', thumb: 'https://assets.coingecko.com/coins/images/44/thumb/xrp-symbol-white-128.png', market_cap_rank: 6 },
    { id: 'usdc', symbol: 'USDC', name: 'USDC', thumb: 'https://assets.coingecko.com/coins/images/6319/thumb/USD_Coin_icon.png', market_cap_rank: 7 },
    { id: 'cardano', symbol: 'ADA', name: 'Cardano', thumb: 'https://assets.coingecko.com/coins/images/975/thumb/cardano.png', market_cap_rank: 8 },
    { id: 'avalanche-2', symbol: 'AVAX', name: 'Avalanche', thumb: 'https://assets.coingecko.com/coins/images/12559/thumb/Avalanche_Circle_RedWhite_Trans.png', market_cap_rank: 9 },
    { id: 'dogecoin', symbol: 'DOGE', name: 'Dogecoin', thumb: 'https://assets.coingecko.com/coins/images/5/thumb/dogecoin.png', market_cap_rank: 10 },
  ]

  return mockTokens.filter(t => 
    t.name.toLowerCase().includes(queryLower) || 
    t.symbol.toLowerCase().includes(queryLower) || 
    t.id.toLowerCase().includes(queryLower)
  )
}

const TokenSearchInput: React.FC<TokenSearchInputProps> = ({ 
  onSelect, 
  placeholder = "Search tokens...", 
  disabled = false 
}) => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<TokenSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length >= 2) {
        setLoading(true)
        setIsOpen(true)
        try {
          const data = await mockSearchTokens(query)
          setResults(data)
          setSelectedIndex(-1) // Reset selection
        } catch (error) {
          console.error("Search failed", error)
          setResults([])
        } finally {
          setLoading(false)
        }
      } else {
        setResults([])
        setIsOpen(false)
      }
    }, 300) // 300ms debounce

    return () => clearTimeout(timer)
  }, [query])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => (prev < results.length - 1 ? prev + 1 : prev))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : prev))
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelect(results[selectedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        inputRef.current?.blur()
        break
    }
  }

  const handleSelect = (token: TokenSearchResult) => {
    onSelect(token)
    setQuery('')
    setIsOpen(false)
    setResults([])
  }

  return (
    <div className="relative w-full" ref={containerRef}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg 
            className="h-5 w-5 text-gray-400" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          ref={inputRef}
          type="text"
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100 disabled:text-gray-500"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (query.length >= 2) setIsOpen(true)
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        {loading && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <svg className="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        )}
      </div>

      {isOpen && (
        <div className="absolute mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm z-50">
          {results.length > 0 ? (
            results.map((token, index) => (
              <div
                key={token.id}
                className={`cursor-pointer select-none relative py-2 pl-3 pr-9 flex items-center ${
                  index === selectedIndex ? 'bg-blue-50 text-blue-900' : 'text-gray-900 hover:bg-gray-50'
                }`}
                onClick={() => handleSelect(token)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="flex items-center">
                  <img src={token.thumb} alt={token.symbol} className="h-6 w-6 rounded-full mr-3" />
                  <div className="flex flex-col">
                    <span className="font-medium block truncate">
                      {token.name} <span className="text-gray-500 font-normal">({token.symbol.toUpperCase()})</span>
                    </span>
                    {token.market_cap_rank && (
                      <span className="text-xs text-gray-400">
                        Rank #{token.market_cap_rank}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="cursor-default select-none relative py-2 px-4 text-gray-700">
              {loading ? 'Searching...' : 'No tokens found.'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default TokenSearchInput
