import type { Env } from '../types/env'
import { getSupabaseClient } from './supabase'
import { CoinGeckoClient } from './coingecko'

export interface PriceAlertConfig {
  token_id: string
  symbol: string
  condition: 'above' | 'below' | 'change_up' | 'change_down'
  target_value: number
  repeat: boolean
}

export interface PriceAlertResult {
  task_id: string
  user_id: string
  triggered: boolean
  current_price: number
  target_value: number
  condition: string
  message: string
}

export async function processPriceAlerts(env: Env): Promise<PriceAlertResult[]> {
  const supabase = getSupabaseClient(env, true)
  const results: PriceAlertResult[] = []

  const { data: tasks, error } = await supabase
    .from('agent_tasks')
    .select('id, user_id, config')
    .eq('task_type', 'price_alert')
    .eq('status', 'active')
    .limit(100)

  if (error || !tasks || tasks.length === 0) {
    console.log('[PriceAlert] No active price alert tasks')
    return results
  }

  const tokenIds = new Set<string>()
  for (const task of tasks) {
    const t = task as { config: unknown }
    const config = t.config as PriceAlertConfig
    if (config?.token_id) {
      tokenIds.add(config.token_id.toLowerCase())
    }
  }

  if (tokenIds.size === 0) return results

  const client = new CoinGeckoClient()
  const prices = await client.getBatchPrices(Array.from(tokenIds))

  for (const task of tasks) {
    const t = task as { id: string; user_id: string; config: unknown }
    const config = t.config as PriceAlertConfig
    if (!config?.token_id) continue

    const priceData = prices.get(config.token_id.toLowerCase())
    if (!priceData) continue

    const { triggered, message } = evaluateCondition(config, priceData.price_usd, priceData.price_change_24h)

    if (triggered) {
      results.push({
        task_id: t.id,
        user_id: t.user_id,
        triggered: true,
        current_price: priceData.price_usd,
        target_value: config.target_value,
        condition: config.condition,
        message,
      })

      await supabase.from('notifications').insert({
        user_id: t.user_id,
        type: 'price_alert',
        title: `价格预警: ${config.symbol}`,
        message,
        data: {
          task_id: t.id,
          symbol: config.symbol,
          current_price: priceData.price_usd,
          target_value: config.target_value,
          condition: config.condition,
        },
      })

      if (!config.repeat) {
        await supabase.from('agent_tasks').update({ status: 'completed' }).eq('id', t.id)
      }
    }
  }

  console.log(`[PriceAlert] Processed ${tasks.length} tasks, ${results.length} triggered`)
  return results
}

function evaluateCondition(
  config: PriceAlertConfig,
  currentPrice: number,
  priceChange24h: number
): { triggered: boolean; message: string } {
  const { condition, target_value, symbol } = config

  switch (condition) {
    case 'above':
      if (currentPrice >= target_value) {
        return {
          triggered: true,
          message: `${symbol} 已突破 $${target_value}，当前价格 $${currentPrice.toFixed(4)}`,
        }
      }
      break
    case 'below':
      if (currentPrice <= target_value) {
        return {
          triggered: true,
          message: `${symbol} 已跌破 $${target_value}，当前价格 $${currentPrice.toFixed(4)}`,
        }
      }
      break
    case 'change_up':
      if (priceChange24h >= target_value) {
        return {
          triggered: true,
          message: `${symbol} 24h 涨幅达 ${priceChange24h.toFixed(2)}%，超过阈值 ${target_value}%`,
        }
      }
      break
    case 'change_down':
      if (priceChange24h <= -target_value) {
        return {
          triggered: true,
          message: `${symbol} 24h 跌幅达 ${Math.abs(priceChange24h).toFixed(2)}%，超过阈值 ${target_value}%`,
        }
      }
      break
  }

  return { triggered: false, message: '' }
}
