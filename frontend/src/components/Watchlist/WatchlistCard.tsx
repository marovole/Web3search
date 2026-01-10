import React from 'react';
import { Bell, Trash2, TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface WatchlistCardProps {
  id: string;
  symbol: string;
  name: string;
  logoUrl?: string;
  price?: number;
  priceChange24h?: number;
  isLoading?: boolean;
  onRemove: (id: string) => void;
  onCreateAlert: (symbol: string) => void;
}

const WatchlistCard: React.FC<WatchlistCardProps> = ({
  id,
  symbol,
  name,
  logoUrl,
  price,
  priceChange24h,
  isLoading = false,
  onRemove,
  onCreateAlert,
}) => {
  // Loading Skeleton State
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 h-[140px] flex flex-col justify-between animate-pulse">
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gray-100" />
            <div className="space-y-2">
              <div className="h-4 w-12 bg-gray-100 rounded" />
              <div className="h-3 w-20 bg-gray-50 rounded" />
            </div>
          </div>
          <div className="h-8 w-8 bg-gray-50 rounded-full" />
        </div>
        <div className="space-y-2">
          <div className="h-6 w-32 bg-gray-100 rounded" />
          <div className="h-4 w-16 bg-gray-50 rounded" />
        </div>
      </div>
    );
  }

  const isPositive = (priceChange24h || 0) >= 0;
  const formattedPrice = price
    ? price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    : '—';
  const formattedChange = priceChange24h
    ? `${isPositive ? '+' : ''}${priceChange24h.toFixed(2)}%`
    : '—';

  return (
    <div className="group relative bg-white rounded-xl shadow-sm border border-gray-200/60 p-5 hover:shadow-lg hover:-translate-y-0.5 hover:border-blue-100 transition-all duration-300 ease-out overflow-hidden">
      {/* Decorative gradient blob for subtle depth */}
      <div className="absolute -top-10 -right-10 w-24 h-24 bg-gradient-to-br from-gray-50 to-gray-100 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative flex flex-col h-full justify-between gap-4">
        {/* Header: Token Info & Actions */}
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3">
            {/* Logo with fallback */}
            <div className="relative w-10 h-10 flex-shrink-0">
              {logoUrl ? (
                <img
                  src={logoUrl}
                  alt={name}
                  className="w-full h-full rounded-full object-cover border border-gray-100 shadow-sm"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.nextElementSibling?.classList.remove('hidden');
                  }}
                />
              ) : null}
              <div
                className={cn(
                  "w-full h-full rounded-full flex items-center justify-center text-sm font-bold bg-gray-50 text-gray-400 border border-gray-100",
                  logoUrl ? "hidden" : ""
                )}
              >
                {symbol.charAt(0)}
              </div>
            </div>

            <div className="flex flex-col">
              <span className="font-bold text-gray-900 leading-tight tracking-tight">
                {symbol}
              </span>
              <span className="text-xs text-gray-500 font-medium truncate max-w-[100px]">
                {name}
              </span>
            </div>
          </div>

          {/* Action Buttons - Visible on Hover/Focus */}
          <div className="flex items-center gap-1 opacity-100 sm:opacity-0 sm:translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200">
            <button
              onClick={() => onCreateAlert(symbol)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
              title="Create Alert"
            >
              <Bell className="w-4 h-4" />
            </button>
            <button
              onClick={() => onRemove(id)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
              title="Remove from Watchlist"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Price Information */}
        <div className="flex flex-col gap-1">
          <div className="text-2xl font-bold text-gray-900 tabular-nums tracking-tight">
            {formattedPrice}
          </div>
          
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border",
                isPositive
                  ? "bg-emerald-50 text-emerald-700 border-emerald-100"
                  : "bg-rose-50 text-rose-700 border-rose-100"
              )}
            >
              {isPositive ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              {formattedChange}
            </div>
            <span className="text-xs text-gray-400 font-medium">24h</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WatchlistCard;
