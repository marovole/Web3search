import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ThemeProvider } from '@/components/theme-provider';
import { BrowserRouter } from 'react-router-dom';

const routerFutureConfig = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

// Custom render function that includes common providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter future={routerFutureConfig}>
      <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
        {children}
      </ThemeProvider>
    </BrowserRouter>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything from Testing Library
export * from '@testing-library/react';
export { customRender as render };

// Helper to render with custom theme
export const renderWithTheme = (
  ui: ReactElement,
  theme: 'light' | 'dark' | 'system' = 'light',
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  const ThemeWrapper = ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter future={routerFutureConfig}>
      <ThemeProvider defaultTheme={theme} storageKey="vite-ui-theme">
        {children}
      </ThemeProvider>
    </BrowserRouter>
  );

  return render(ui, { wrapper: ThemeWrapper, ...options });
};

// Helper to render with router
export const renderWithRouter = (
  ui: ReactElement,
  initialEntries = ['/'],
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  const RouterWrapper = ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter future={routerFutureConfig}>
      <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
        {children}
      </ThemeProvider>
    </BrowserRouter>
  );

  return render(ui, { wrapper: RouterWrapper, ...options });
};
