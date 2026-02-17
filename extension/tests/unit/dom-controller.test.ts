/**
 * Unit tests for DOM controller
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { domController } from '../../src/content/dom-controller';

describe('DOMController', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('should navigate to URL', async () => {
    const result = await domController.navigate({
      url: 'https://example.com',
    });

    expect(result.success).toBe(true);
    expect(result.url).toBe('https://example.com');
  });

  it('should scroll page', async () => {
    const result = await domController.scroll({
      direction: 'down',
      amount: 100,
    });

    expect(result.success).toBe(true);
    expect(result.direction).toBe('down');
  });

  it('should extract text from element', async () => {
    document.body.innerHTML = '<div id="test">Hello World</div>';

    const result = await domController.extractText({
      selector: '#test',
    });

    expect(result.text).toBe('Hello World');
  });

  it('should extract links from page', async () => {
    document.body.innerHTML = '<a href="https://example.com">Link</a>';

    const result = await domController.extractLinks({});

    expect(result.links).toHaveLength(1);
    expect(result.links[0].href).toContain('example.com');
  });

  it('should get DOM structure', async () => {
    document.body.innerHTML = '<div id="test">Content</div>';

    const result = await domController.getDOM({});

    expect(result.html).toContain('test');
  });

  it('should highlight element', async () => {
    document.body.innerHTML = '<div id="test">Content</div>';

    const result = await domController.highlightElement({
      selector: '#test',
      duration_ms: 1000,
    });

    expect(result.success).toBe(true);
  });
});
