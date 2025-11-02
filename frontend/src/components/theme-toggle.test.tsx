import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeToggle } from './theme-toggle';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockClear();
    document.documentElement.className = '';
  });

  it('renders theme toggle button', () => {
    render(<ThemeToggle />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('has correct accessibility label', () => {
    render(<ThemeToggle />);
    expect(screen.getByText('切换主题')).toBeInTheDocument();
  });

  it('opens dropdown menu when clicked', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    
    await user.click(button);
    
    expect(screen.getByText('浅色')).toBeInTheDocument();
    expect(screen.getByText('深色')).toBeInTheDocument();
    expect(screen.getByText('跟随系统')).toBeInTheDocument();
  });

  it('sets theme to light when light option is clicked', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    
    await user.click(button);
    await user.click(screen.getByText('浅色'));
    
    expect(document.documentElement).toHaveClass('light');
  });

  it('sets theme to dark when dark option is clicked', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    
    await user.click(button);
    await user.click(screen.getByText('深色'));
    
    expect(document.documentElement).toHaveClass('dark');
  });

  it('sets theme to system when system option is clicked', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    
    await user.click(button);
    await user.click(screen.getByText('跟随系统'));
    
    // When theme is system, it should apply the system preference (light in our mock)
    expect(document.documentElement).toHaveClass('light');
  });

  it('loads theme from localStorage on mount', () => {
    localStorageMock.getItem.mockReturnValue('dark');
    
    render(<ThemeToggle />);
    
    expect(document.documentElement).toHaveClass('dark');
  });

  it('defaults to system theme when no theme in localStorage', () => {
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<ThemeToggle />);
    
    expect(localStorageMock.getItem).toHaveBeenCalledWith('theme');
  });
});
