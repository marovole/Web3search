import React, { useState, useEffect } from 'react';
import { Bell, X, TrendingUp, TrendingDown, AlertCircle, ArrowRight, Check } from 'lucide-react';
import { cn } from '@/lib/utils'; // Assuming cn utility exists based on project structure

interface PriceAlertFormProps {
  symbol: string;
  name: string;
  currentPrice?: number;
  onSubmit: (alert: {
    symbol: string;
    condition: 'above' | 'below' | 'percent_up' | 'percent_down';
    threshold: number;
  }) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

type ConditionType = 'above' | 'below' | 'percent_up' | 'percent_down';

const PriceAlertForm: React.FC<PriceAlertFormProps> = ({
  symbol,
  name,
  currentPrice = 0,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [condition, setCondition] = useState<ConditionType>('above');
  const [threshold, setThreshold] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Set initial threshold based on condition and current price
  useEffect(() => {
    if (!threshold && currentPrice > 0) {
      if (condition === 'above') {
        setThreshold((currentPrice * 1.05).toFixed(2));
      } else if (condition === 'below') {
        setThreshold((currentPrice * 0.95).toFixed(2));
      } else {
        setThreshold('5'); // Default 5%
      }
    }
  }, [condition, currentPrice]);

  const validate = (val: string, cond: ConditionType): string | null => {
    const num = parseFloat(val);
    if (isNaN(num)) return 'Please enter a valid number';
    if (num < 0) return 'Value must be positive';
    
    if (cond === 'percent_up' || cond === 'percent_down') {
      if (num > 1000) return 'Percentage cannot exceed 1000%';
    }
    
    return null;
  };

  const handleThresholdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setThreshold(val);
    setError(validate(val, condition));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validate(threshold, condition);
    if (validationError) {
      setError(validationError);
      return;
    }
    onSubmit({
      symbol,
      condition,
      threshold: parseFloat(threshold),
    });
  };

  const getPreviewText = () => {
    const val = parseFloat(threshold);
    if (isNaN(val)) return '...';

    const formattedPrice = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(val);

    switch (condition) {
      case 'above':
        return `Alert when ${symbol} rises above ${formattedPrice}`;
      case 'below':
        return `Alert when ${symbol} drops below ${formattedPrice}`;
      case 'percent_up':
        return `Alert when ${symbol} goes up by ${val}%`;
      case 'percent_down':
        return `Alert when ${symbol} goes down by ${val}%`;
    }
  };

  const formatCurrentPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  return (
    <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100 font-sans animate-in fade-in zoom-in-95 duration-200">
      {/* Header */}
      <div className="bg-slate-50/50 p-6 border-b border-slate-100 flex justify-between items-start">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl">
            <Bell size={20} strokeWidth={2.5} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 leading-tight">Price Alert</h3>
            <p className="text-sm text-slate-500 font-medium">Get notified instantly</p>
          </div>
        </div>
        <button 
          onClick={onCancel}
          className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      <div className="p-6 space-y-8">
        {/* Token Info Card */}
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
              {symbol[0]}
            </div>
            <div>
              <div className="font-bold text-slate-900">{symbol}</div>
              <div className="text-xs font-medium text-slate-500">{name}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-slate-500">Current Price</div>
            <div className="font-mono font-bold text-slate-900">{formatCurrentPrice(currentPrice)}</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Condition Selector */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Condition</label>
            <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
              <button
                type="button"
                onClick={() => setCondition('above')}
                className={cn(
                  "flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-bold transition-all duration-200",
                  condition === 'above' 
                    ? "bg-white text-emerald-600 shadow-sm ring-1 ring-black/5" 
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                <TrendingUp size={16} /> Above
              </button>
              <button
                type="button"
                onClick={() => setCondition('below')}
                className={cn(
                  "flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-bold transition-all duration-200",
                  condition === 'below' 
                    ? "bg-white text-rose-600 shadow-sm ring-1 ring-black/5" 
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                <TrendingDown size={16} /> Below
              </button>
              <button
                type="button"
                onClick={() => setCondition('percent_up')}
                className={cn(
                  "flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-bold transition-all duration-200",
                  condition === 'percent_up' 
                    ? "bg-white text-emerald-600 shadow-sm ring-1 ring-black/5" 
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                <span className="text-base leading-none">%</span> Up
              </button>
              <button
                type="button"
                onClick={() => setCondition('percent_down')}
                className={cn(
                  "flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-bold transition-all duration-200",
                  condition === 'percent_down' 
                    ? "bg-white text-rose-600 shadow-sm ring-1 ring-black/5" 
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                <span className="text-base leading-none">%</span> Down
              </button>
            </div>
          </div>

          {/* Threshold Input */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              {condition.includes('percent') ? 'Percentage Change' : 'Target Price (USD)'}
            </label>
            <div className="relative group">
              <input
                type="number"
                step={condition.includes('percent') ? "0.1" : "0.000001"}
                value={threshold}
                onChange={handleThresholdChange}
                placeholder="0.00"
                className={cn(
                  "w-full px-4 py-4 bg-slate-50 border-2 rounded-xl text-2xl font-bold text-slate-900 outline-none transition-all duration-200 placeholder:text-slate-300",
                  error 
                    ? "border-rose-200 focus:border-rose-500 focus:bg-white" 
                    : "border-slate-100 group-hover:border-slate-200 focus:border-indigo-500 focus:bg-white focus:shadow-[0_0_0_4px_rgba(99,102,241,0.1)]"
                )}
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                {condition.includes('percent') ? (
                  <span className="text-slate-400 font-bold text-xl">%</span>
                ) : (
                  <span className="text-slate-400 font-bold text-xl">$</span>
                )}
              </div>
            </div>
            {error && (
              <div className="flex items-center gap-2 text-rose-500 text-sm font-medium animate-in slide-in-from-left-2 fade-in duration-200">
                <AlertCircle size={14} />
                {error}
              </div>
            )}
          </div>

          {/* Live Preview */}
          <div className="p-4 bg-indigo-50/50 rounded-xl border border-indigo-100/50 flex items-start gap-3">
            <div className="mt-0.5 min-w-[20px] text-indigo-500">
              <ArrowRight size={18} />
            </div>
            <div>
              <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-0.5">Summary</div>
              <div className="text-indigo-900 font-medium leading-relaxed">
                {getPreviewText()}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-3.5 bg-white border-2 border-slate-100 text-slate-600 font-bold rounded-xl hover:bg-slate-50 hover:border-slate-200 transition-all duration-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !!error || !threshold}
              className={cn(
                "flex-1 px-4 py-3.5 bg-slate-900 text-white font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-slate-900/10 transition-all duration-200",
                (isLoading || !!error || !threshold)
                  ? "opacity-50 cursor-not-allowed"
                  : "hover:translate-y-[-1px] hover:shadow-xl hover:shadow-slate-900/20 active:translate-y-[1px]"
              )}
            >
              {isLoading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Check size={18} strokeWidth={3} />
                  Create Alert
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PriceAlertForm;
