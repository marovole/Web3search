import { act, waitFor, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Custom test helpers
export const testHelpers = {
  // Wait for element to appear and be visible
  waitForElement: async (testId: string, timeout = 5000) => {
    return waitFor(() => {
      const element = screen.getByTestId(testId);
      expect(element).toBeInTheDocument();
      expect(element).toBeVisible();
      return element;
    }, { timeout });
  },

  // Wait for loading to complete
  waitForLoadingToComplete: async (loadingTestId = 'loading') => {
    return waitFor(() => {
      const loadingElement = screen.queryByTestId(loadingTestId);
      expect(loadingElement).not.toBeInTheDocument();
    });
  },

  // Fill form fields
  fillForm: async (fields: Record<string, string>) => {
    const user = userEvent.setup();
    
    for (const [testId, value] of Object.entries(fields)) {
      const element = screen.getByTestId(testId);
      await user.clear(element);
      await user.type(element, value);
    }
  },

  // Submit form and wait for response
  submitFormAndWait: async (submitTestId = 'submit-button', loadingTestId = 'loading') => {
    const user = userEvent.setup();
    
    await user.click(screen.getByTestId(submitTestId));
    
    if (loadingTestId) {
      await this.waitForLoadingToComplete(loadingTestId);
    }
  },

  // Test error message display
  testErrorMessage: async (message: string, errorTestId = 'error-message') => {
    const errorElement = await screen.findByTestId(errorTestId);
    expect(errorElement).toBeInTheDocument();
    expect(errorElement).toHaveTextContent(message);
  },

  // Test success message display
  testSuccessMessage: async (message: string, successTestId = 'success-message') => {
    const successElement = await screen.findByTestId(successTestId);
    expect(successElement).toBeInTheDocument();
    expect(successElement).toHaveTextContent(message);
  },

  // Test that element has specific CSS classes
  testElementClasses: (testId: string, expectedClasses: string[]) => {
    const element = screen.getByTestId(testId);
    expectedClasses.forEach(className => {
      expect(element).toHaveClass(className);
    });
  },

  // Test that element is disabled
  testElementDisabled: (testId: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toBeDisabled();
  },

  // Test that element is enabled
  testElementEnabled: (testId: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toBeEnabled();
  },

  // Test accessibility attributes
  testA11yAttributes: (testId: string, attributes: Record<string, string>) => {
    const element = screen.getByTestId(testId);
    
    Object.entries(attributes).forEach(([attr, value]) => {
      expect(element).toHaveAttribute(attr, value);
    });
  },

  // Test that element has correct ARIA role
  testRole: (testId: string, role: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toHaveAttribute('role', role);
  },

  // Test that element is focused
  testFocused: (testId: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toHaveFocus();
  },

  // Wait for API call to complete (mock)
  waitForApiCall: async (mockFn: jest.Mock, timeout = 5000) => {
    return waitFor(() => {
      expect(mockFn).toHaveBeenCalled();
    }, { timeout });
  },

  // Test number of API calls
  testApiCallCount: (mockFn: jest.Mock, expectedCount: number) => {
    expect(mockFn).toHaveBeenCalledTimes(expectedCount);
  },

  // Test API call with specific parameters
  testApiCallWith: (mockFn: jest.Mock, expectedParams: any) => {
    expect(mockFn).toHaveBeenCalledWith(expectedParams);
  },

  // Create a delay for testing async behavior
  delay: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),

  // Test that component renders children correctly
  testChildren: (testId: string, expectedChildren: string[]) => {
    const element = screen.getByTestId(testId);
    expectedChildren.forEach(childText => {
      expect(element).toHaveTextContent(childText);
    });
  },

  // Test that element has correct text content
  testTextContent: (testId: string, expectedText: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toHaveTextContent(expectedText);
  },

  // Test that element does not contain text
  testNotContainsText: (testId: string, forbiddenText: string) => {
    const element = screen.getByTestId(testId);
    expect(element).not.toHaveTextContent(forbiddenText);
  },

  // Test responsive behavior (mock window resize)
  testResponsive: async (testId: string, width: number, height: number) => {
    // Mock window resize
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: width,
    });
    
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: height,
    });

    await act(async () => {
      // Trigger resize event
      window.dispatchEvent(new Event('resize'));
      // Wait for any debounced resize handlers
      await testHelpers.delay(100);
    });
  },

  // Test localStorage interactions
  testLocalStorage: {
    setItem: (key: string, value: string) => {
      localStorage.setItem(key, value);
    },
    
    getItem: (key: string) => {
      return localStorage.getItem(key);
    },
    
    removeItem: (key: string) => {
      localStorage.removeItem(key);
    },
    
    clear: () => {
      localStorage.clear();
    },
    
    testItemExists: (key: string, expectedValue: string) => {
      expect(localStorage.getItem(key)).toBe(expectedValue);
    },
    
    testItemNotExists: (key: string) => {
      expect(localStorage.getItem(key)).toBeNull();
    },
  },

  // Test sessionStorage interactions
  testSessionStorage: {
    setItem: (key: string, value: string) => {
      sessionStorage.setItem(key, value);
    },
    
    getItem: (key: string) => {
      return sessionStorage.getItem(key);
    },
    
    removeItem: (key: string) => {
      sessionStorage.removeItem(key);
    },
    
    clear: () => {
      sessionStorage.clear();
    },
    
    testItemExists: (key: string, expectedValue: string) => {
      expect(sessionStorage.getItem(key)).toBe(expectedValue);
    },
    
    testItemNotExists: (key: string) => {
      expect(sessionStorage.getItem(key)).toBeNull();
    },
  },
};

// Re-export commonly used helpers
export const {
  waitForElement,
  waitForLoadingToComplete,
  fillForm,
  submitFormAndWait,
  testErrorMessage,
  testSuccessMessage,
  testElementClasses,
  testElementDisabled,
  testElementEnabled,
  testA11yAttributes,
  testRole,
  testFocused,
  waitForApiCall,
  testApiCallCount,
  testApiCallWith,
  delay,
  testChildren,
  testTextContent,
  testNotContainsText,
  testResponsive,
} = testHelpers;
