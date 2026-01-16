import { test, expect } from '@playwright/test'

const API_BASE_URL = process.env.E2E_API_BASE_URL || process.env.VITE_API_BASE_URL || 'https://web3search-api.marovole.workers.dev/api/v1'
const AUTH_TOKEN = process.env.E2E_AUTH_TOKEN

const getAuthHeaders = () => ({
  Authorization: `Bearer ${AUTH_TOKEN}`,
  'Content-Type': 'application/json',
})

test('price alert notification endpoints respond', async ({ request }) => {
  if (!AUTH_TOKEN) {
    throw new Error('E2E_AUTH_TOKEN is required to run price alert notification test')
  }

  const createResponse = await request.post(`${API_BASE_URL}/agents/tasks`, {
    headers: getAuthHeaders(),
    data: {
      name: 'E2E Price Alert Notification',
      description: 'Price alert for notification test',
      type: 'price_alert',
      config: { token: 'BTC', condition: 'below', target_price: 10000 },
    },
  })

  expect([200, 201]).toContain(createResponse.status())
  const createBody = await createResponse.json()
  const taskId = createBody.task?.id

  const notificationsResponse = await request.get(`${API_BASE_URL}/notifications`, {
    headers: getAuthHeaders(),
  })

  expect(notificationsResponse.ok()).toBeTruthy()

  const pushTestResponse = await request.post(`${API_BASE_URL}/push/test`, {
    headers: getAuthHeaders(),
  })

  expect(pushTestResponse.ok()).toBeTruthy()

  if (taskId) {
    await request.delete(`${API_BASE_URL}/agents/tasks/${taskId}`, {
      headers: getAuthHeaders(),
    })
  }
})
