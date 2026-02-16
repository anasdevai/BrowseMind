/**
 * Element selector utilities for finding DOM elements.
 * Supports CSS selectors and text-based matching.
 */

export interface SelectorOptions {
  selector?: string;
  text?: string;
  index?: number;
}

export class ElementSelector {
  /**
   * Find element(s) matching the given criteria.
   */
  findElement(options: SelectorOptions): Element | null {
    const { selector, text, index = 0 } = options;

    if (selector && text) {
      // Both selector and text: find by selector, then filter by text
      const elements = Array.from(document.querySelectorAll(selector));
      const matches = elements.filter((el) =>
        this.elementContainsText(el, text)
      );
      return matches[index] || null;
    }

    if (selector) {
      // Selector only
      const elements = document.querySelectorAll(selector);
      return elements[index] || null;
    }

    if (text) {
      // Text only: search all clickable elements
      const clickable = this.findClickableElements();
      const matches = clickable.filter((el) =>
        this.elementContainsText(el, text)
      );
      return matches[index] || null;
    }

    return null;
  }

  /**
   * Find all elements matching the given criteria.
   */
  findElements(options: SelectorOptions): Element[] {
    const { selector, text } = options;

    if (selector && text) {
      const elements = Array.from(document.querySelectorAll(selector));
      return elements.filter((el) => this.elementContainsText(el, text));
    }

    if (selector) {
      return Array.from(document.querySelectorAll(selector));
    }

    if (text) {
      const clickable = this.findClickableElements();
      return clickable.filter((el) => this.elementContainsText(el, text));
    }

    return [];
  }

  /**
   * Check if element contains the given text.
   */
  private elementContainsText(element: Element, text: string): boolean {
    const elementText = element.textContent?.trim().toLowerCase() || "";
    const searchText = text.trim().toLowerCase();
    return elementText.includes(searchText);
  }

  /**
   * Find all clickable elements (buttons, links, inputs).
   */
  private findClickableElements(): Element[] {
    const selectors = [
      "button",
      "a",
      "input[type='button']",
      "input[type='submit']",
      "[role='button']",
      "[onclick]",
    ];

    const elements: Element[] = [];
    for (const selector of selectors) {
      elements.push(...Array.from(document.querySelectorAll(selector)));
    }

    return elements;
  }

  /**
   * Get element's visible text content.
   */
  getElementText(element: Element, trim: boolean = true): string {
    const text = element.textContent || "";
    return trim ? text.trim() : text;
  }

  /**
   * Check if element is visible.
   */
  isElementVisible(element: Element): boolean {
    if (!(element instanceof HTMLElement)) {
      return false;
    }

    const style = window.getComputedStyle(element);
    return (
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      style.opacity !== "0" &&
      element.offsetParent !== null
    );
  }

  /**
   * Wait for element to appear in DOM.
   */
  async waitForElement(
    options: SelectorOptions,
    timeoutMs: number = 5000
  ): Promise<Element | null> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      const element = this.findElement(options);
      if (element && this.isElementVisible(element)) {
        return element;
      }
      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    return null;
  }
}

export const elementSelector = new ElementSelector();
