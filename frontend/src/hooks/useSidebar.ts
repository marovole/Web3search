import { useState, useEffect } from 'react'

interface SidebarState {
  isOpen: boolean
  isMobile: boolean
  toggle: () => void
  open: () => void
  close: () => void
  setIsMobile: (isMobile: boolean) => void
}

const STORAGE_KEY = 'sidebar-open-state'

export const useSidebar = (initialState: boolean = false): SidebarState => {
  // Load state from localStorage on mount
  const [isOpen, setIsOpen] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved !== null ? JSON.parse(saved) : initialState
    }
    return initialState
  })

  const [isMobile, setIsMobile] = useState(false)

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)

      // Auto-close sidebar on mobile
      if (mobile && isOpen) {
        setIsOpen(false)
      }
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [isOpen])

  // Save state to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(isOpen))
    }
  }, [isOpen])

  const toggle = () => setIsOpen(!isOpen)
  const open = () => setIsOpen(true)
  const close = () => setIsOpen(false)

  return {
    isOpen,
    isMobile,
    toggle,
    open,
    close,
    setIsMobile
  }
}