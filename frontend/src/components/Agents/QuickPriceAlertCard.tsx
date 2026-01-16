import React from 'react'
import { Bell, TrendingDown, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface QuickPriceAlertCardProps {
  symbol: string
  threshold: string
  onSymbolChange: (value: string) => void
  onThresholdChange: (value: string) => void
  onSubmit: () => void
  isSubmitting?: boolean
  error?: string | null
  className?: string
}

export const QuickPriceAlertCard: React.FC<QuickPriceAlertCardProps> = ({
  symbol,
  threshold,
  onSymbolChange,
  onThresholdChange,
  onSubmit,
  isSubmitting = false,
  error = null,
  className
}) => {
  const isFormValid = symbol.trim() !== '' && threshold !== '' && parseFloat(threshold) > 0

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && isFormValid && !isSubmitting) {
      e.preventDefault()
      onSubmit()
    }
  }

  return (
    <Card className={cn("border-primary/20 bg-primary/5", className)}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Bell className="w-5 h-5 text-primary" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3">
              <TrendingDown className="w-4 h-4 text-yellow-500" />
              <h3 className="text-sm font-semibold">提醒我当价格下跌</h3>
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <Input
                variant="default"
                size="sm"
                placeholder="代币符号 (如 BTC)"
                value={symbol}
                onChange={(e) => onSymbolChange(e.target.value.toUpperCase())}
                onKeyDown={handleKeyDown}
                className="h-9"
                disabled={isSubmitting}
              />
              <Input
                variant="default"
                size="sm"
                type="number"
                step="0.000001"
                placeholder="目标价格 ($)"
                value={threshold}
                onChange={(e) => onThresholdChange(e.target.value)}
                onKeyDown={handleKeyDown}
                className="h-9"
                disabled={isSubmitting}
              />
            </div>

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive" className="mb-3 py-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <AlertDescription className="text-xs">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            {/* Submit Button */}
            <Button
              size="sm"
              variant="default"
              onClick={onSubmit}
              disabled={!isFormValid || isSubmitting}
              className="w-full"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  创建中...
                </>
              ) : (
                <>
                  <Bell className="w-4 h-4 mr-2" />
                  创建价格预警
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default QuickPriceAlertCard
