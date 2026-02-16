/**
 * DOM controller for browser automation.
 * Executes tool commands in the page context.
 */

import { elementSelector, type SelectorOptions } from "./element-selector";

export interface NavigateParams {
  url: string;
  wait_until?: "load" | "domcontentloaded" | "networkidle";
  timeout_ms?: number;
}

export interface ClickParams {
  selector?: string;
  text?: string;
  index?: number;
  wait_for_navigation?: boolean;
}

export interface TypeParams {
  selector: string;
  text: string;
  clear_first?: boolean;
  press_enter?: boolean;
}

export interface ScrollParams {
  direction: "up" | "down" | "top" | "bottom";
  amount?: number;
  smooth?: boolean;
}

export interface ExtractTextParams {
  selector: string;
  all?: boolean;
  trim?: boolean;
}

export interface ExtractLinksParams {
  selector?: string;
  filter_pattern?: string;
}

export interface ScreenshotParams {
  selector?: string;
  full_page?: boolean;
  format?: "png" | "jpeg";
}

export interface GetDOMParams {
  selector?: string;
  depth?: number;
}

export interface HighlightParams {
  selector: string;
  duration_ms?: number;
}

export class DOMController {
  /**
   * Navigate to a URL.
   */
  async navigate(params: NavigateParams): Promise<{ success: boolean; url: string }> {
    try {
      window.location.href = params.url;
      return { success: true, url: params.url };
    } catch (error) {
      throw new Error(`Navigation failed: ${error.message}`);
    }
  }

  /**
   * Click an element.
   */
  async clickElement(params: ClickParams): Promise<{ success: boolean; element: string }> {
    const element = elementSelector.findElement({
      selector: params.selector,
      text: params.text,
      index: params.index || 0,
    });

    if (!element) {
      throw new Error(
        `Element not found: ${params.selector || params.text}`
      );
    }

    if (!elementSelector.isElementVisible(element)) {
      throw new Error("Element is not visible");
    }

    if (element instanceof HTMLElement) {
      element.click();
      return {
        success: true,
        element: params.selector || params.text || "unknown",
      };
    }

    throw new Error("Element is not clickable");
  }

  /**
   * Type text into an input field.
   */
  async typeText(params: TypeParams): Promise<{ success: boolean; text: string }> {
    const element = elementSelector.findElement({
      selector: params.selector,
    });

    if (!element) {
      throw new Error(`Input element not found: ${params.selector}`);
    }

    if (
      !(element instanceof HTMLInputElement) &&
      !(element instanceof HTMLTextAreaElement)
    ) {
      throw new Error("Element is not an input field");
    }

    // Clear existing text if requested
    if (params.clear_first !== false) {
      element.value = "";
    }

    // Type text
    element.value += params.text;

    // Trigger input event
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));

    // Press Enter if requested
    if (params.press_enter) {
      element.dispatchEvent(
        new KeyboardEvent("keydown", { key: "Enter", bubbles: true })
      );
    }

    return { success: true, text: params.text };
  }

  /**
   * Scroll the page.
   */
  async scroll(params: ScrollParams): Promise<{ success: boolean; direction: string }> {
    const behavior = params.smooth !== false ? "smooth" : "auto";

    switch (params.direction) {
      case "top":
        window.scrollTo({ top: 0, behavior });
        break;
      case "bottom":
        window.scrollTo({ top: document.body.scrollHeight, behavior });
        break;
      case "up":
        window.scrollBy({ top: -(params.amount || 500), behavior });
        break;
      case "down":
        window.scrollBy({ top: params.amount || 500, behavior });
        break;
    }

    return { success: true, direction: params.direction };
  }

  /**
   * Extract text from element(s).
   */
  async extractText(params: ExtractTextParams): Promise<{ text: string | string[] }> {
    if (params.all) {
      const elements = elementSelector.findElements({
        selector: params.selector,
      });
      const texts = elements.map((el) =>
        elementSelector.getElementText(el, params.trim !== false)
      );
      return { text: texts };
    } else {
      const element = elementSelector.findElement({
        selector: params.selector,
      });
      if (!element) {
        throw new Error(`Element not found: ${params.selector}`);
      }
      const text = elementSelector.getElementText(element, params.trim !== false);
      return { text };
    }
  }

  /**
   * Extract links from the page.
   */
  async extractLinks(params: ExtractLinksParams): Promise<{ links: Array<{ text: string; href: string }> }> {
    const selector = params.selector || "a[href]";
    const elements = elementSelector.findElements({ selector });

    const links = elements
      .filter((el) => el instanceof HTMLAnchorElement)
      .map((el) => {
        const anchor = el as HTMLAnchorElement;
        return {
          text: elementSelector.getElementText(anchor, true),
          href: anchor.href,
        };
      });

    // Apply filter pattern if provided
    if (params.filter_pattern) {
      const regex = new RegExp(params.filter_pattern);
      return {
        links: links.filter((link) => regex.test(link.href)),
      };
    }

    return { links };
  }

  /**
   * Get DOM structure.
   */
  async getDOM(params: GetDOMParams): Promise<{ html: string }> {
    const element = params.selector
      ? elementSelector.findElement({ selector: params.selector })
      : document.documentElement;

    if (!element) {
      throw new Error(`Element not found: ${params.selector}`);
    }

    return { html: element.outerHTML };
  }

  /**
   * Highlight an element visually.
   */
  async highlightElement(params: HighlightParams): Promise<{ success: boolean }> {
    const element = elementSelector.findElement({
      selector: params.selector,
    });

    if (!element || !(element instanceof HTMLElement)) {
      throw new Error(`Element not found: ${params.selector}`);
    }

    // Store original style
    const originalOutline = element.style.outline;
    const originalZIndex = element.style.zIndex;

    // Apply highlight
    element.style.outline = "3px solid #ff6b6b";
    element.style.zIndex = "9999";

    // Remove highlight after duration
    const duration = params.duration_ms || 2000;
    setTimeout(() => {
      element.style.outline = originalOutline;
      element.style.zIndex = originalZIndex;
    }, duration);

    return { success: true };
  }

  /**
   * Capture screenshot (delegated to background script).
   */
  async screenshot(params: ScreenshotParams): Promise<{ dataUrl: string }> {
    // This will be handled by the background script via chrome.tabs.captureVisibleTab
    // Content script just returns a message to trigger it
    throw new Error("Screenshot must be handled by background script");
  }
}

export const domController = new DOMController();
