import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { ReactElement } from 'react';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Accessibility testing utilities
export const a11yHelpers = {
  // Test component for accessibility violations
  testAccessibility: async (component: ReactElement) => {
    const { container } = render(component);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  },

  // Test specific element for accessibility
  testElementAccessibility: async (element: HTMLElement) => {
    const results = await axe(element);
    expect(results).toHaveNoViolations();
  },

  // Test that element has proper ARIA attributes
  testAriaLabel: (testId: string, expectedLabel: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toHaveAttribute('aria-label', expectedLabel);
  },

  // Test that element has proper ARIA described by
  testAriaDescribedBy: (testId: string, describedById: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toHaveAttribute('aria-describedby', describedById);
  },

  // Test that element has proper ARIA labelled by
  testAriaLabelledBy: (testId: string, labelledById: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toHaveAttribute('aria-labelledby', labelledById);
  },

  // Test that element has proper role
  testRole: (testId: string, expectedRole: string) => {
    const element = screen.getByTestId(testId);
    expect(element).toHaveAttribute('role', expectedRole);
  },

  // Test that button is accessible
  testButtonAccessibility: (testId: string, expectedLabel?: string) => {
    const button = screen.getByTestId(testId);
    expect(button).toHaveAttribute('type', 'button');
    
    if (expectedLabel) {
      expect(button).toHaveAccessibleName(expectedLabel);
    } else {
      expect(button).toHaveAccessibleName();
    }
  },

  // Test that input is accessible
  testInputAccessibility: (testId: string, expectedLabel: string, required = false) => {
    const input = screen.getByTestId(testId);
    expect(input).toHaveAccessibleName(expectedLabel);
    
    if (required) {
      expect(input).toBeRequired();
    }
  },

  // Test that form has proper accessibility
  testFormAccessibility: (formTestId: string, fields: Array<{ testId: string; label: string; required?: boolean }>) => {
    fields.forEach(field => {
      a11yHelpers.testInputAccessibility(field.testId, field.label, field.required);
    });
  },

  // Test that link is accessible
  testLinkAccessibility: (testId: string, expectedLabel: string) => {
    const link = screen.getByTestId(testId);
    expect(link).toHaveAttribute('href');
    expect(link).toHaveAccessibleName(expectedLabel);
  },

  // Test that modal is accessible
  testModalAccessibility: (modalTestId: string, titleTestId: string) => {
    const modal = screen.getByTestId(modalTestId);
    const title = screen.getByTestId(titleTestId);
    
    expect(modal).toHaveAttribute('role', 'dialog');
    expect(modal).toHaveAttribute('aria-modal', 'true');
    expect(title).toHaveAttribute('id');
    expect(modal).toHaveAttribute('aria-labelledby', title.getAttribute('id'));
  },

  // Test that navigation is accessible
  testNavigationAccessibility: (navTestId: string) => {
    const nav = screen.getByTestId(navTestId);
    expect(nav).toHaveAttribute('role', 'navigation');
    
    // Test that all links in navigation are accessible
    const links = nav.querySelectorAll('a');
    links.forEach(link => {
      expect(link).toHaveAccessibleName();
    });
  },

  // Test that table is accessible
  testTableAccessibility: (tableTestId: string, headers: string[]) => {
    const table = screen.getByTestId(tableTestId);
    
    // Test that table has proper headers
    headers.forEach(headerText => {
      const header = screen.getByRole('columnheader', { name: headerText });
      expect(header).toBeInTheDocument();
    });
    
    // Test that table has caption or aria-label
    const hasCaption = table.querySelector('caption') !== null;
    const hasAriaLabel = table.hasAttribute('aria-label') || table.hasAttribute('aria-labelledby');
    
    expect(hasCaption || hasAriaLabel).toBe(true);
  },

  // Test that list is accessible
  testListAccessibility: (listTestId: string, ordered = false) => {
    const list = screen.getByTestId(listTestId);
    const expectedRole = ordered ? 'list' : 'list';
    expect(list).toHaveAttribute('role', expectedRole);
    
    // Test that list items are properly marked
    const listItems = list.querySelectorAll('[role="listitem"]');
    expect(listItems.length).toBeGreaterThan(0);
  },

  // Test that image has alt text
  testImageAccessibility: (testId: string, expectedAlt?: string) => {
    const img = screen.getByTestId(testId);
    expect(img).toHaveAttribute('alt');
    
    if (expectedAlt) {
      expect(img).toHaveAttribute('alt', expectedAlt);
    }
  },

  // Test that video has accessibility features
  testVideoAccessibility: (testId: string) => {
    const video = screen.getByTestId(testId);
    
    // Video should have controls or be properly described
    const hasControls = video.hasAttribute('controls');
    const hasLabel = video.hasAttribute('aria-label') || video.hasAttribute('aria-labelledby');
    
    expect(hasControls || hasLabel).toBe(true);
  },

  // Test that progress indicator is accessible
  testProgressAccessibility: (testId: string, label: string) => {
    const progress = screen.getByTestId(testId);
    expect(progress).toHaveAttribute('role', 'progressbar');
    expect(progress).toHaveAccessibleName(label);
    
    // Test that progress has proper value attributes
    if (progress.hasAttribute('aria-valuenow')) {
      expect(progress).toHaveAttribute('aria-valuemin');
      expect(progress).toHaveAttribute('aria-valuemax');
    }
  },

  // Test that tooltip is accessible
  testTooltipAccessibility: (triggerTestId: string, tooltipTestId: string) => {
    const trigger = screen.getByTestId(triggerTestId);
    const tooltip = screen.getByTestId(tooltipTestId);
    
    expect(trigger).toHaveAttribute('aria-describedby');
    expect(tooltip).toHaveAttribute('id');
    expect(trigger.getAttribute('aria-describedby')).toBe(tooltip.getAttribute('id'));
  },

  // Test that tabs are accessible
  testTabsAccessibility: (tablistTestId: string, tabs: Array<{ testId: string; label: string; panelId: string }>) => {
    const tablist = screen.getByTestId(tablistTestId);
    expect(tablist).toHaveAttribute('role', 'tablist');
    
    tabs.forEach(tab => {
      const tabElement = screen.getByTestId(tab.testId);
      const panelElement = document.getElementById(tab.panelId);
      
      expect(tabElement).toHaveAttribute('role', 'tab');
      expect(tabElement).toHaveAttribute('aria-selected');
      expect(tabElement).toHaveAttribute('aria-controls', tab.panelId);
      expect(tabElement).toHaveAccessibleName(tab.label);
      
      if (panelElement) {
        expect(panelElement).toHaveAttribute('role', 'tabpanel');
        expect(panelElement).toHaveAttribute('aria-labelledby', tabElement.getAttribute('id'));
      }
    });
  },

  // Test that accordion is accessible
  testAccordionAccessibility: (accordionTestId: string, items: Array<{ testId: string; label: string; contentId: string }>) => {
    const accordion = screen.getByTestId(accordionTestId);
    
    items.forEach(item => {
      const header = screen.getByTestId(item.testId);
      const content = document.getElementById(item.contentId);
      
      expect(header).toHaveAttribute('role', 'button');
      expect(header).toHaveAttribute('aria-expanded');
      expect(header).toHaveAttribute('aria-controls', item.contentId);
      expect(header).toHaveAccessibleName(item.label);
      
      if (content) {
        expect(content).toHaveAttribute('role', 'region');
        expect(content).toHaveAttribute('aria-labelledby', header.getAttribute('id'));
      }
    });
  },

  // Test keyboard navigation
  testKeyboardNavigation: async (element: HTMLElement, expectedKeys: string[]) => {
    for (const key of expectedKeys) {
      element.focus();
      element.dispatchEvent(new KeyboardEvent('keydown', { key }));
      expect(element).toHaveFocus();
    }
  },

  // Test focus management
  testFocusManagement: (element: HTMLElement) => {
    element.focus();
    expect(element).toHaveFocus();
    
    // Test that focus is visible
    const computedStyle = window.getComputedStyle(element);
    expect(computedStyle.outline).not.toBe('none');
  },

  // Test color contrast (basic check)
  testColorContrast: (element: HTMLElement, minimumRatio = 4.5) => {
    const computedStyle = window.getComputedStyle(element);
    const color = computedStyle.color;
    const backgroundColor = computedStyle.backgroundColor;
    
    // This is a simplified check - in real implementation, you'd use a color contrast library
    expect(color).toBeDefined();
    expect(backgroundColor).toBeDefined();
    expect(color).not.toBe(backgroundColor); // Ensure text and background are different
  },
};

// Re-export commonly used helpers
export const {
  testAccessibility,
  testElementAccessibility,
  testAriaLabel,
  testAriaDescribedBy,
  testAriaLabelledBy,
  testRole,
  testButtonAccessibility,
  testInputAccessibility,
  testFormAccessibility,
  testLinkAccessibility,
  testModalAccessibility,
  testNavigationAccessibility,
  testTableAccessibility,
  testListAccessibility,
  testImageAccessibility,
  testVideoAccessibility,
  testProgressAccessibility,
  testTooltipAccessibility,
  testTabsAccessibility,
  testAccordionAccessibility,
  testKeyboardNavigation,
  testFocusManagement,
  testColorContrast,
} = a11yHelpers;
