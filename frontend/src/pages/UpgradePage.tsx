import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PricingTable } from '../components/Billing/PricingTable'
import { useAuth } from '../contexts/AuthContext'
import { createCheckoutSession, createPortalSession } from '../services/api'
import { useToast } from '../components/ui/toast'
import { Loader2, AlertCircle, HelpCircle, Mail, ChevronDown } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"

const UpgradePage: React.FC = () => {
  const { user, profile, loading: authLoading } = useAuth()
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()
  const navigate = useNavigate()

  const handleUpgrade = async (plan: 'pro' | 'team', interval: 'monthly' | 'yearly') => {
    if (!user) {
      navigate('/auth/login?redirect=/upgrade')
      return
    }

    setLoading(true)
    try {
      const { checkout_url } = await createCheckoutSession(plan, interval)
      window.location.href = checkout_url
    } catch (error) {
      console.error('Checkout error:', error)
      toast({
        title: "Checkout failed",
        description: error instanceof Error ? error.message : "Please try again later",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const handleManage = async () => {
    setLoading(true)
    try {
      const { portal_url } = await createPortalSession()
      window.location.href = portal_url
    } catch (error) {
      console.error('Portal error:', error)
      toast({
        title: "Access failed",
        description: "Could not access billing portal. Please try again.",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const faqs = [
    {
      q: "What happens when I upgrade?",
      a: "Your account will be instantly upgraded to the new plan limits. You'll get immediate access to advanced features like Deep Research and increased daily quotas."
    },
    {
      q: "Can I cancel anytime?",
      a: "Yes, you can cancel your subscription at any time. Your benefits will continue until the end of your current billing period."
    },
    {
      q: "How does the \"2 months free\" work?",
      a: "When you choose annual billing, you pay for 10 months and get 12 months of access. That's a ~17% discount compared to monthly billing."
    },
    {
      q: "Do you offer refunds?",
      a: "We offer a 7-day money-back guarantee for all new Pro and Team subscriptions if you're not satisfied with the service."
    }
  ]

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-slate-950 py-16 md:py-24">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
        <div className="relative container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-primary/20 text-primary hover:bg-primary/30 border-primary/20">
            Upgrade Your Experience
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60 mb-6">
            Unlock the Full Power of Web3 Research
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            Get unlimited access to AI agents, deep research reports, and real-time market alerts. 
            Make smarter investment decisions faster.
          </p>
        </div>
      </div>

      {/* Pricing Table */}
      <div className="-mt-12 relative z-10 mb-20">
        <PricingTable
          currentPlan={profile?.plan || 'free'}
          onUpgrade={handleUpgrade}
          onManage={handleManage}
          loading={loading}
        />
      </div>

      {/* FAQ Section */}
      <div className="container mx-auto px-4 max-w-3xl mb-20">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold mb-4">Frequently Asked Questions</h2>
          <p className="text-muted-foreground">Everything you need to know about our pricing and plans.</p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <details key={i} className="group bg-muted/30 rounded-lg border border-border open:bg-muted/50 transition-all duration-200">
              <summary className="flex items-center justify-between p-4 cursor-pointer font-medium select-none list-none [&::-webkit-details-marker]:hidden">
                {faq.q}
                <ChevronDown className="w-4 h-4 text-muted-foreground transition-transform duration-200 group-open:rotate-180" />
              </summary>
              <div className="px-4 pb-4 text-muted-foreground pt-0 animate-in fade-in slide-in-from-top-1 duration-200">
                {faq.a}
              </div>
            </details>
          ))}
        </div>
      </div>

      {/* Contact / Help */}
      <div className="container mx-auto px-4 max-w-3xl text-center">
        <div className="bg-muted/50 rounded-2xl p-8 border border-border">
          <div className="flex flex-col items-center gap-4">
            <div className="p-3 bg-background rounded-full">
              <HelpCircle className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-xl font-semibold">Still have questions?</h3>
            <p className="text-muted-foreground mb-4">
              Our support team is here to help you find the perfect plan for your needs.
            </p>
            <Button variant="outline" className="gap-2" onClick={() => window.location.href = 'mailto:support@web3search.com'}>
              <Mail className="w-4 h-4" />
              Contact Support
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UpgradePage

