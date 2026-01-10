import React, { useState } from 'react';
import { Shield, AlertTriangle, X, Check, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RiskMonitorFormProps {
  symbol: string;
  name: string;
  onSubmit: (config: {
    symbol: string;
    monitor_scam_score: boolean;
    monitor_red_flags: boolean;
    sensitivity: 'any' | 'significant' | 'major';
  }) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

type Sensitivity = 'any' | 'significant' | 'major';

const RiskMonitorForm: React.FC<RiskMonitorFormProps> = ({
  symbol,
  name,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [monitorScamScore, setMonitorScamScore] = useState(true);
  const [monitorRedFlags, setMonitorRedFlags] = useState(true);
  const [sensitivity, setSensitivity] = useState<Sensitivity>('significant');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      symbol,
      monitor_scam_score: monitorScamScore,
      monitor_red_flags: monitorRedFlags,
      sensitivity,
    });
  };

  const getPreviewText = () => {
    if (!monitorScamScore && !monitorRedFlags) return 'Please select at least one monitoring option.';

    const parts = [];
    if (monitorScamScore) {
      const sensitivityText = {
        any: 'any score changes',
        significant: 'significant score changes (±10)',
        major: 'major score changes (±20)'
      }[sensitivity];
      parts.push(sensitivityText);
    }
    
    if (monitorRedFlags) {
      parts.push('new red flags');
    }

    return `Monitor ${symbol} for ${parts.join(' and ')}.`;
  };

  return (
    <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100 font-sans animate-in fade-in zoom-in-95 duration-200">
      {/* Header */}
      <div className="bg-slate-50/50 p-6 border-b border-slate-100 flex justify-between items-start">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-orange-50 text-orange-600 rounded-xl">
            <Shield size={20} strokeWidth={2.5} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 leading-tight">Risk Monitor</h3>
            <p className="text-sm text-slate-500 font-medium">Track security changes</p>
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
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
              {symbol[0]}
            </div>
            <div>
              <div className="font-bold text-slate-900">{symbol}</div>
              <div className="text-xs font-medium text-slate-500">{name}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="px-2.5 py-1 bg-orange-100 text-orange-700 text-xs font-bold rounded-lg uppercase tracking-wider">
              Security
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Monitoring Options */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">What to Monitor</label>
            <div className="space-y-2">
              <label className={cn(
                "flex items-center gap-3 p-3 rounded-xl border-2 transition-all duration-200 cursor-pointer",
                monitorScamScore 
                  ? "border-orange-500 bg-orange-50/30" 
                  : "border-slate-100 hover:border-slate-200"
              )}>
                <input 
                  type="checkbox"
                  checked={monitorScamScore}
                  onChange={(e) => setMonitorScamScore(e.target.checked)}
                  className="w-5 h-5 rounded text-orange-600 focus:ring-orange-500 border-slate-300"
                />
                <div className="flex-1">
                  <div className="text-sm font-bold text-slate-900">ScamMeter Score</div>
                  <div className="text-xs text-slate-500">Track changes in risk score</div>
                </div>
              </label>

              <label className={cn(
                "flex items-center gap-3 p-3 rounded-xl border-2 transition-all duration-200 cursor-pointer",
                monitorRedFlags
                  ? "border-orange-500 bg-orange-50/30" 
                  : "border-slate-100 hover:border-slate-200"
              )}>
                <input 
                  type="checkbox"
                  checked={monitorRedFlags}
                  onChange={(e) => setMonitorRedFlags(e.target.checked)}
                  className="w-5 h-5 rounded text-orange-600 focus:ring-orange-500 border-slate-300"
                />
                <div className="flex-1">
                  <div className="text-sm font-bold text-slate-900">Red Flags</div>
                  <div className="text-xs text-slate-500">Alert on new warning signs</div>
                </div>
              </label>
            </div>
          </div>

          {/* Sensitivity Selector */}
          {monitorScamScore && (
            <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Sensitivity</label>
              <div className="grid grid-cols-3 gap-2 p-1 bg-slate-100 rounded-xl">
                {(['any', 'significant', 'major'] as const).map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setSensitivity(option)}
                    className={cn(
                      "py-2 px-2 rounded-lg text-xs font-bold transition-all duration-200 capitalize",
                      sensitivity === option 
                        ? "bg-white text-orange-600 shadow-sm ring-1 ring-black/5" 
                        : "text-slate-500 hover:text-slate-700"
                    )}
                  >
                    {option}
                  </button>
                ))}
              </div>
              <div className="text-xs text-slate-400 font-medium px-1">
                {sensitivity === 'any' && 'Alert on any score change (±1 point)'}
                {sensitivity === 'significant' && 'Alert on moderate changes (±10 points)'}
                {sensitivity === 'major' && 'Alert only on large changes (±20 points)'}
              </div>
            </div>
          )}

          {/* Live Preview */}
          <div className="p-4 bg-orange-50/50 rounded-xl border border-orange-100/50 flex items-start gap-3">
            <div className="mt-0.5 min-w-[20px] text-orange-500">
              <ArrowRight size={18} />
            </div>
            <div>
              <div className="text-xs font-bold text-orange-400 uppercase tracking-wider mb-0.5">Summary</div>
              <div className="text-orange-900 font-medium leading-relaxed text-sm">
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
              disabled={isLoading || (!monitorScamScore && !monitorRedFlags)}
              className={cn(
                "flex-1 px-4 py-3.5 bg-slate-900 text-white font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-slate-900/10 transition-all duration-200",
                (isLoading || (!monitorScamScore && !monitorRedFlags))
                  ? "opacity-50 cursor-not-allowed"
                  : "hover:translate-y-[-1px] hover:shadow-xl hover:shadow-slate-900/20 active:translate-y-[1px]"
              )}
            >
              {isLoading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Check size={18} strokeWidth={3} />
                  Start Monitor
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RiskMonitorForm;
