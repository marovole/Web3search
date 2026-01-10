export interface CheckoutRequest {
  plan: 'pro' | 'team'
  interval: 'monthly' | 'yearly'
}

export interface CheckoutResponse {
  checkout_url: string
}

export interface PortalResponse {
  portal_url: string
}

export interface PlanFeature {
  name: string
  included: boolean
  limit?: string
}

export interface PricingTier {
  id: 'free' | 'pro' | 'team'
  name: string
  description: string
  price: {
    monthly: number
    yearly: number
  }
  features: PlanFeature[]
  highlight?: boolean
  buttonText: string
}
