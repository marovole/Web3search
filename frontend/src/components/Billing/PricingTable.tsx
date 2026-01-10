import React, { useState } from 'react'
import { Check, X, Zap, Shield, Infinity, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export interface PricingTableProps {
  currentPlan?: 'free' | 'pro' | 'team'
  onUpgrade: (plan: 'pro' | 'team', interval: 'monthly' | 'yearly') => Promise<void>
  onManage: () => Promise<void>
  loading?: boolean
}

export const PricingTable: React.FC<PricingTableProps> = ({
  currentPlan = 'free',
  onUpgrade,
  onManage,
  loading = false
}) => {
  const [interval, setInterval] = useState<'monthly' | 'yearly'>('monthly')
  const [processingPlan, setProcessingPlan] = useState<string | null>(null)

  const handleAction = async (plan: 'free' | 'pro' | 'team') => {
    if (plan === currentPlan) {
      if (plan !== 'free') {
        setProcessingPlan(plan)
        try {
          await onManage()
        } finally {
          setProcessingPlan(null)
        }
      }
      return
    }

    if (plan === 'free') return // Cannot downgrade to free via this UI usually

    setProcessingPlan(plan)
    try {
      await onUpgrade(plan, interval)
    } finally {
      setProcessingPlan(null)
    }
  }

  const tiers = [
    {
      id: 'free',
      name: 'Starter',
      description: 'Essential tools for crypto enthusiasts',
      price: { monthly: 0, yearly: 0 },
      icon: Zap,
      features: [
        { name: '5 Watchlist items', included: true },
        { name: '3 Agent tasks / day', included: true },
        { name: '10 Daily alerts', included: true },
        { name: '5 Deep Research / day', included: true },
        { name: 'Basic support', included: true },
        { name: 'API Access', included: false },
      ]
    },
    {
      id: 'pro',
      name: 'Pro',
      description: 'Advanced power for serious investors',
      price: { monthly: 9.9, yearly: 99 },
      icon: Shield,
      highlight: true,
      features: [
        { name: '50 Watchlist items', included: true },
        { name: '20 Agent tasks / day', included: true },
        { name: '100 Daily alerts', included: true },
        { name: '50 Deep Research / day', included: true },
        { name: 'Priority support', included: true },
        { name: 'Early access to new features', included: true },
      ]
    },
    {
      id: 'team',
      name: 'Team',
      description: 'Unrestricted access for professional teams',
      price: { monthly: 29.9, yearly: 299 },
      icon: Infinity,
      features: [
        { name: 'Unlimited Watchlist', included: true },
        { name: '100 Agent tasks / day', included: true },
        { name: 'Unlimited alerts', included: true },
        { name: 'Unlimited Deep Research', included: true },
        { name: 'Dedicated support', included: true },
        { name: 'Full API Access', included: true },
      ]
    }
  ] as const

  return (
    <div className="w-full max-w-7xl mx-auto px-4 py-8">
      {/* Header & Toggle */}
      <div className="text-center mb-12 space-y-4">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
          Simple, transparent pricing
        </h2>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
          Choose the perfect plan for your trading style. Unlock advanced AI capabilities and deep market insights.
        </p>
        
        <div className="flex items-center justify-center mt-8">
          <div className="bg-muted/50 p-1 rounded-full inline-flex items-center border border-border">
            <button
              onClick={() => setInterval('monthly')}
              className={cn(
                "px-6 py-2 rounded-full text-sm font-medium transition-all duration-200",
                interval === 'monthly' 
                  ? "bg-background shadow-sm text-foreground ring-1 ring-border" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              )}
            >
              Monthly
            </button>
            <button
              onClick={() => setInterval('yearly')}
              className={cn(
                "px-6 py-2 rounded-full text-sm font-medium transition-all duration-200 flex items-center gap-2",
                interval === 'yearly' 
                  ? "bg-background shadow-sm text-foreground ring-1 ring-border" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              )}
            >
              Yearly
              <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20 text-[10px] px-1.5 h-5">
                2 months free
              </Badge>
            </button>
          </div>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
        {tiers.map((tier) => {
          const isCurrent = currentPlan === tier.id
          const isPro = tier.id === 'pro'
          const Icon = tier.icon
          const price = interval === 'monthly' ? tier.price.monthly : tier.price.yearly
          const isProcessing = processingPlan === tier.id

          return (
            <div
              key={tier.id}
              className={cn(
                "relative rounded-2xl p-8 transition-all duration-200",
                "bg-card border backdrop-blur-sm",
                isPro 
                  ? "border-primary/50 shadow-2xl shadow-primary/10 scale-105 z-10" 
                  : "border-border hover:border-primary/30",
                isCurrent && "ring-2 ring-primary ring-offset-2 ring-offset-background"
              )}
            >
              {isPro && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <Badge className="bg-primary text-primary-foreground px-4 py-1">
                    Most Popular
                  </Badge>
                </div>
              )}

              <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                  <div className={cn(
                    "p-3 rounded-xl w-fit",
                    isPro ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
                  )}>
                    <Icon className="w-6 h-6" />
                  </div>
                  {isCurrent && (
                    <Badge variant="outline" className="border-primary text-primary">
                      Current Plan
                    </Badge>
                  )}
                </div>
                
                <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
                <p className="text-muted-foreground text-sm h-10">{tier.description}</p>
              </div>

              <div className="mb-8">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold">${price}</span>
                  <span className="text-muted-foreground">/{interval === 'monthly' ? 'mo' : 'yr'}</span>
                </div>
                {interval === 'yearly' && tier.price.monthly > 0 && (
                  <p className="text-xs text-muted-foreground mt-2">
                    Billed ${price} yearly
                  </p>
                )}
              </div>

              <Button
                className={cn(
                  "w-full mb-8",
                  isPro ? "btn-primary" : "btn-secondary"
                )}
                variant={isPro ? "default" : "outline"}
                disabled={loading || (isCurrent && tier.id === 'free')}
                onClick={() => handleAction(tier.id)}
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : null}
                {isCurrent 
                  ? (tier.id === 'free' ? 'Current Plan' : 'Manage Subscription')
                  : (tier.id === 'free' ? 'Downgrade' : 'Upgrade')
                }
              </Button>

              <div className="space-y-4">
                <p className="text-sm font-medium">Includes:</p>
                <ul className="space-y-3">
                  {tier.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-sm">
                      {feature.included ? (
                        <Check className="w-5 h-5 text-primary shrink-0" />
                      ) : (
                        <X className="w-5 h-5 text-muted-foreground/30 shrink-0" />
                      )}
                      <span className={cn(
                        !feature.included && "text-muted-foreground/50"
                      )}>
                        {feature.name}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
