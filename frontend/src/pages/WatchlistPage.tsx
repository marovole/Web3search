import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApiWatchlist } from '../hooks/useApiWatchlist'
import { useAuth } from '../contexts/AuthContext'
import TokenSearchInput, { TokenSearchResult } from '../components/Watchlist/TokenSearchInput'
import WatchlistCard from '../components/Watchlist/WatchlistCard'
import api from '../services/api'

interface PriceData {
  price_usd: number
  price_change_24h: number
}

const WatchlistPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated, session } = useAuth()
  const { watchlist, loading, error, addToWatchlist, removeFromWatchlist, clearWatchlist } = useApiWatchlist()
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [prices, setPrices] = useState<Record<string, PriceData>>({})
  const [pricesLoading, setPricesLoading] = useState(false)

  const fetchPrices = useCallback(async () => {
    if (watchlist.length === 0) {
      setPrices({})
      return
    }

    setPricesLoading(true)
    try {
      const symbols = watchlist.map(item => item.coingecko_id || item.symbol.toLowerCase())
      const response = await api.get('/api/v1/prices/batch', {
        params: { ids: symbols.join(',') },
        headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}
      })
      
      if (response.data.prices) {
        const priceMap: Record<string, PriceData> = {}
        for (const [id, data] of Object.entries(response.data.prices)) {
          const priceData = data as { usd?: number; usd_24h_change?: number }
          priceMap[id] = {
            price_usd: priceData.usd || 0,
            price_change_24h: priceData.usd_24h_change || 0
          }
        }
        setPrices(priceMap)
      }
    } catch (err) {
      console.error('[Watchlist] Failed to fetch prices:', err)
    } finally {
      setPricesLoading(false)
    }
  }, [watchlist, session?.access_token])

  useEffect(() => {
    if (watchlist.length > 0) {
      fetchPrices()
      const interval = setInterval(fetchPrices, 30000)
      return () => clearInterval(interval)
    }
  }, [fetchPrices, watchlist.length])

  const handleAddToken = async (token: TokenSearchResult) => {
    const success = await addToWatchlist({
      token_id: token.id,
      symbol: token.symbol.toUpperCase(),
      name: token.name,
      coingecko_id: token.id,
      logo_url: token.thumb,
    })
    
    if (success) {
      fetchPrices()
    }
  }

  const handleRemove = async (id: string) => {
    await removeFromWatchlist(id)
  }

  const handleCreateAlert = (symbol: string) => {
    navigate(`/agent-chat?action=create-alert&symbol=${symbol}`)
  }

  const handleClearWatchlist = async () => {
    if (showClearConfirm) {
      await clearWatchlist()
      setShowClearConfirm(false)
    } else {
      setShowClearConfirm(true)
    }
  }

  const getPrice = (item: { coingecko_id?: string; symbol: string }): PriceData | undefined => {
    const key = item.coingecko_id || item.symbol.toLowerCase()
    return prices[key]
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Sign In Required</h2>
          <p className="text-gray-600 mb-6">Please sign in to manage your watchlist</p>
          <button onClick={() => navigate('/login')} className="btn-primary">
            Sign In
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-gray-900">My Watchlist</h1>
            <span className="text-sm text-gray-500">{watchlist.length} / 20</span>
          </div>

          {watchlist.length > 0 && (
            <button
              onClick={handleClearWatchlist}
              className={`px-4 py-2 rounded-lg transition-colors ${
                showClearConfirm
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'text-red-600 hover:bg-red-50'
              }`}
            >
              {showClearConfirm ? 'Confirm Clear' : 'Clear All'}
            </button>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8 max-w-md">
          <TokenSearchInput
            onSelect={handleAddToken}
            placeholder="Search tokens to add..."
            disabled={watchlist.length >= 20}
          />
          {watchlist.length >= 20 && (
            <p className="text-sm text-amber-600 mt-2">Watchlist is full (max 20 tokens)</p>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <WatchlistCard
                key={i}
                id=""
                symbol=""
                name=""
                isLoading={true}
                onRemove={() => {}}
                onCreateAlert={() => {}}
              />
            ))}
          </div>
        ) : watchlist.length === 0 ? (
          <div className="text-center py-20">
            <svg
              className="w-24 h-24 mx-auto text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
              />
            </svg>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">No tokens yet</h2>
            <p className="text-gray-600 mb-6">
              Search and add tokens above to start tracking
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {watchlist.map(item => {
              const priceData = getPrice(item)
              return (
                <WatchlistCard
                  key={item.id}
                  id={item.id}
                  symbol={item.symbol}
                  name={item.name}
                  logoUrl={item.logo_url}
                  price={priceData?.price_usd}
                  priceChange24h={priceData?.price_change_24h}
                  isLoading={pricesLoading && !priceData}
                  onRemove={handleRemove}
                  onCreateAlert={handleCreateAlert}
                />
              )
            })}
          </div>
        )}

        {showClearConfirm && (
          <div className="mt-4 text-center">
            <button
              onClick={() => setShowClearConfirm(false)}
              className="text-gray-600 hover:text-gray-900"
            >
              Cancel
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default WatchlistPage
