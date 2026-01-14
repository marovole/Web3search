import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeToggle } from './theme-toggle';

const mockSetTheme = jest.fn();

jest.mock('./theme-provider', () => ({
  useTheme: () => ({
    setTheme: mockSetTheme,
  }),
}));

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
    mockSetTheme.mockClear();
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
    
    expect(mockSetTheme).toHaveBeenCalledWith('light');
  });

  it('sets theme to dark when dark option is clicked', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    
    await user.click(button);
    await user.click(screen.getByText('深色'));
    
    expect(mockSetTheme).toHaveBeenCalledWith('dark');
  });

  it('sets theme to system when system option is clicked', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    
    await user.click(button);
    await user.click(screen.getByText('跟随系统'));
    
    expect(mockSetTheme).toHaveBeenCalledWith('system');
  });

  it('does not call setTheme on initial render', () => {
    render(<ThemeToggle />);

    expect(mockSetTheme).not.toHaveBeenCalled();
  });
});
