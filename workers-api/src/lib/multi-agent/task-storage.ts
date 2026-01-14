/**
 * Multi-Agent Task Storage using Cloudflare KV
 * Replaces Supabase for task persistence
 */

import type { Env } from '../../types/env'
import type { TaskStatus, TaskIntent, TaskConfig } from './types'

export interface TaskRecord {
  id: string
  userId: string
  query: string
  intent: TaskIntent
  config: TaskConfig
  status: TaskStatus
  result: string | null
  error: string | null
  tokensUsed: number
  durationMs: number
  startedAt: string | null
  completedAt: string | null
  createdAt: string
  updatedAt: string
}

export interface TaskStorage {
  createTask(task: Omit<TaskRecord, 'createdAt' | 'updatedAt'>): Promise<TaskRecord>
  updateTask(id: string, updates: Partial<TaskRecord>): Promise<TaskRecord | null>
  getTask(id: string): Promise<TaskRecord | null>
  getUserTasks(userId: string, limit?: number, offset?: number): Promise<TaskRecord[]>
  deleteTask(id: string): Promise<boolean>
}

export class KvTaskStorage implements TaskStorage {
  private readonly KV_PREFIX = 'task:'
  private readonly USER_TASKS_PREFIX = 'user_tasks:'
  private readonly TTL = 7 * 24 * 60 * 60 // 7 days

  constructor(private readonly kv: KVNamespace | undefined) {}

  async createTask(task: Omit<TaskRecord, 'createdAt' | 'updatedAt'>): Promise<TaskRecord> {
    const now = new Date().toISOString()
    const record: TaskRecord = {
      ...task,
      createdAt: now,
      updatedAt: now,
    }

    const key = this.getTaskKey(task.id)

    // Store task
    await this.kv?.put(key, JSON.stringify(record), { expirationTtl: this.TTL })

    // Add to user's task list (sorted by creation time, newest first)
    const userTasksKey = this.USER_TASKS_PREFIX + task.userId
    const existing = await this.kv?.get(userTasksKey) as string | null
    const taskIds = existing ? JSON.parse(existing) : []
    taskIds.unshift(task.id)

    // Keep only last 100 tasks per user
    const trimmedIds = taskIds.slice(0, 100)
    await this.kv?.put(userTasksKey, JSON.stringify(trimmedIds), { expirationTtl: this.TTL })

    return record
  }

  async updateTask(id: string, updates: Partial<TaskRecord>): Promise<TaskRecord | null> {
    const existing = await this.getTask(id)
    if (!existing) return null

    const updated: TaskRecord = {
      ...existing,
      ...updates,
      updatedAt: new Date().toISOString(),
    }

    const key = this.getTaskKey(id)
    await this.kv?.put(key, JSON.stringify(updated), { expirationTtl: this.TTL })

    return updated
  }

  async getTask(id: string): Promise<TaskRecord | null> {
    const key = this.getTaskKey(id)
    const data = await this.kv?.get(key)
    if (!data) return null
    return JSON.parse(data) as TaskRecord
  }

  async getUserTasks(userId: string, limit = 20, offset = 0): Promise<TaskRecord[]> {
    const userTasksKey = this.USER_TASKS_PREFIX + userId
    const data = await this.kv?.get(userTasksKey)
    if (!data) return []

    const taskIds: string[] = JSON.parse(data)
    const paginatedIds = taskIds.slice(offset, offset + limit)

    const tasks: TaskRecord[] = []
    for (const id of paginatedIds) {
      const task = await this.getTask(id)
      if (task) tasks.push(task)
    }

    return tasks
  }

  async deleteTask(id: string): Promise<boolean> {
    const task = await this.getTask(id)
    if (!task) return false

    const key = this.getTaskKey(id)
    await this.kv?.delete(key)

    // Remove from user's task list
    const userTasksKey = this.USER_TASKS_PREFIX + task.userId
    const data = await this.kv?.get(userTasksKey)
    if (data) {
      const taskIds: string[] = JSON.parse(data)
      const filtered = taskIds.filter((tid) => tid !== id)
      await this.kv?.put(userTasksKey, JSON.stringify(filtered), { expirationTtl: this.TTL })
    }

    return true
  }

  private getTaskKey(id: string): string {
    return this.KV_PREFIX + id
  }

  private getUserTasksKey(userId: string, taskId: string): string {
    return this.USER_TASKS_PREFIX + userId + ':' + taskId
  }
}

export function createTaskStorage(env: Env): KvTaskStorage {
  return new KvTaskStorage(env.MULTI_AGENT_TASKS)
}
