/**
 * Holdings/Portfolio Page
 * Displays user's crypto portfolio with real-time value tracking
 */

import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useHoldings, HoldingWithValue } from '../hooks/useHoldings'
import { useDiagnosis } from '../hooks/useDiagnosis'
import { AddHoldingModal, DiagnosisReport } from '../components/Holdings'

type TabType = 'holdings' | 'diagnosis'

const HoldingsPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const { 
    holdings, 
    summary, 
    loading, 
    deleteHolding,
    refresh
  } = useHoldings()
  const {
    latestDiagnosis,
    loading: diagnosisLoading,
    fetchLatest: fetchDiagnosis
  } = useDiagnosis()

  const [activeTab, setActiveTab] = useState<TabType>('holdings')
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Auto-refresh summary when holdings change or component mounts
  useEffect(() => {
    if (isAuthenticated) {
      refresh()
    }
  }, [isAuthenticated, refresh])

  useEffect(() => {
    if (isAuthenticated && activeTab === 'diagnosis' && !latestDiagnosis) {
      fetchDiagnosis()
    }
  }, [isAuthenticated, activeTab, latestDiagnosis, fetchDiagnosis])

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (window.confirm('确定要删除这个持仓记录吗？')) {
      try {
        setDeletingId(id)
        await deleteHolding(id)
      } finally {
        setDeletingId(null)
      }
    }
  }

  // Auth Guard
  if (!isAuthenticated && !loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">需要登录</h2>
          <p className="text-gray-600 mb-6">
            请登录后查看您的持仓组合。追踪资产价值、分析盈亏状况。
          </p>
          <button
            onClick={() => navigate('/auth/login')}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            立即登录
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
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
            <div>
              <h1 className="text-2xl font-bold text-gray-900">我的持仓</h1>
              <p className="text-xs text-gray-500 mt-1">
                {loading ? '更新中...' : `共 ${holdings.length} 个代币`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('holdings')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === 'holdings'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                持仓
              </button>
              <button
                onClick={() => setActiveTab('diagnosis')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === 'diagnosis'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                诊断
              </button>
            </div>

            {activeTab === 'holdings' && (
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 shadow-sm"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                添加持仓
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {activeTab === 'holdings' ? (
          <>
            {/* Portfolio Summary Card */}
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-lg p-8 text-white relative overflow-hidden">
              <div className="absolute top-0 right-0 p-32 bg-white/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
              
              <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                  <div className="text-blue-100 text-sm font-medium mb-1">总资产估值 (USD)</div>
                  <div className="text-4xl font-bold tracking-tight">
                    ${summary?.total_value_usd?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                  </div>
                </div>
                
                <div className="hidden md:block border-l border-white/10 pl-8">
                  <div className="text-blue-100 text-sm font-medium mb-1">资产数量</div>
                  <div className="text-2xl font-semibold">
                    {holdings.length} <span className="text-base font-normal text-blue-200">Tokens</span>
                  </div>
                </div>

                <div className="hidden md:block border-l border-white/10 pl-8">
                  <div className="text-blue-100 text-sm font-medium mb-1">今日变动 (估算)</div>
                  <div className="flex items-center gap-2">
                     <span className="text-2xl font-semibold text-white/90">--</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Holdings List */}
            {loading && holdings.length === 0 ? (
               <div className="flex flex-col items-center justify-center py-20">
                 <svg className="animate-spin w-10 h-10 text-blue-600 mb-4" fill="none" viewBox="0 0 24 24">
                   <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                   <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                 </svg>
                 <p className="text-gray-500">正在加载持仓数据...</p>
               </div>
            ) : holdings.length === 0 ? (
              <div className="text-center py-20 bg-white rounded-xl border border-gray-200 border-dashed">
                <div className="w-24 h-24 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6">
                  <svg className="w-12 h-12 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">暂无持仓</h2>
                <p className="text-gray-600 mb-8 max-w-md mx-auto">
                  添加您的第一个加密货币持仓，开始追踪您的投资组合价值和收益。
                </p>
                <button
                  onClick={() => setIsAddModalOpen(true)}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                >
                  添加第一个持仓
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {holdings.map((holding: HoldingWithValue) => {
                  const currentPrice = holding.price_usd || 0
                  const value = holding.value_usd || (holding.quantity * currentPrice)
                  const costBasis = (holding.avg_buy_price || 0) * holding.quantity
                  const pnl = costBasis > 0 ? value - costBasis : 0
                  const pnlPercent = costBasis > 0 ? (pnl / costBasis) * 100 : 0
                  const isProfit = pnl >= 0

                  return (
                    <div 
                      key={holding.id}
                      className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden group"
                    >
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            {holding.logo_url ? (
                              <img 
                                src={holding.logo_url} 
                                alt={holding.symbol} 
                                className="w-10 h-10 rounded-full bg-gray-50"
                              />
                            ) : (
                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center text-blue-600 font-bold text-sm">
                                {holding.symbol.slice(0, 2)}
                              </div>
                            )}
                            <div>
                              <h3 className="font-bold text-gray-900">{holding.symbol}</h3>
                              <p className="text-xs text-gray-500">{holding.name}</p>
                            </div>
                          </div>
                          
                          <div className="text-right">
                            <div className="font-medium text-gray-900">
                              {holding.quantity.toLocaleString('en-US', { maximumFractionDigits: 8 })}
                            </div>
                            <div className="text-xs text-gray-500">数量</div>
                          </div>
                        </div>

                        <div className="space-y-3 py-3 border-t border-gray-50">
                          <div className="flex justify-between items-baseline">
                            <span className="text-sm text-gray-500">当前价值</span>
                            <span className="text-lg font-bold text-gray-900">
                              ${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                          </div>
                          
                          <div className="flex justify-between items-center text-sm">
                            <span className="text-gray-500">现价</span>
                            <div className="text-right">
                              <div className="font-mono text-gray-700">
                                ${currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })}
                              </div>
                              {holding.change_24h !== undefined && (
                                 <div className={`text-xs ${holding.change_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                   {holding.change_24h >= 0 ? '+' : ''}{holding.change_24h.toFixed(2)}% (24h)
                                 </div>
                              )}
                            </div>
                          </div>

                          {holding.avg_buy_price && holding.avg_buy_price > 0 && (
                            <>
                              <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-500">成本价</span>
                                <span className="font-mono text-gray-700">
                                  ${holding.avg_buy_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                </span>
                              </div>
                              
                              <div className="flex justify-between items-center text-sm pt-2 border-t border-dashed border-gray-100">
                                <span className="text-gray-500">盈亏</span>
                                <div className={`flex items-center gap-1 font-medium ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                                  <span>{isProfit ? '+' : ''}{pnl.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span>
                                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${isProfit ? 'bg-green-50' : 'bg-red-50'}`}>
                                    {isProfit ? '+' : ''}{pnlPercent.toFixed(2)}%
                                  </span>
                                </div>
                              </div>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="px-6 py-3 bg-gray-50 flex items-center justify-between text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                         <span className="text-xs text-gray-400">
                            {holding.notes ? '有备注' : '无备注'}
                         </span>
                         <div className="flex gap-3">
                            <button 
                              onClick={(e) => handleDelete(holding.id, e)}
                              disabled={deletingId === holding.id}
                              className="text-red-600 hover:text-red-700 font-medium disabled:opacity-50"
                            >
                              {deletingId === holding.id ? '删除中...' : '删除'}
                            </button>
                         </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </>
        ) : (
          <>
            {diagnosisLoading ? (
              <div className="flex flex-col items-center justify-center py-20">
                <svg className="animate-spin w-10 h-10 text-indigo-600 mb-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <p className="text-gray-500">正在加载诊断报告...</p>
              </div>
            ) : latestDiagnosis ? (
              <DiagnosisReport diagnosis={latestDiagnosis} />
            ) : (
              <div className="text-center py-20 bg-white rounded-xl border border-gray-200 border-dashed">
                <div className="w-24 h-24 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-6">
                  <svg className="w-12 h-12 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">暂无诊断报告</h2>
                <p className="text-gray-600 mb-4 max-w-md mx-auto">
                  添加至少2个持仓后，系统将在每周一自动生成投资组合诊断报告。
                </p>
                <p className="text-sm text-gray-500">
                  诊断报告包含：健康评分、多样化分析、风险评估、投资建议等。
                </p>
              </div>
            )}
          </>
        )}
      </main>

      <AddHoldingModal 
        isOpen={isAddModalOpen} 
        onClose={() => setIsAddModalOpen(false)} 
      />
    </div>
  )
}

export default HoldingsPage
