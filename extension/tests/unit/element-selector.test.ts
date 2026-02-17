/**
 * Unit tests for element selector
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { elementSelector } from '../../src/content/element-selector';

describe('ElementSelector', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('should find element by CSS selector', () => {
    document.body.innerHTML = '<div id="test">Content</div>';

    const element = elementSelector.findElement({
      selector: '#test',
    });

    expect(element).not.toBeNull();
    expect(element?.id).toBe('test');
  });

  it('should find element by text', () => {
    document.body.innerHTML = '<button>Click Me</button>';

    const element = elementSelector.findElement({
      text: 'Click Me',
    });

    expect(element).not.toBeNull();
    expect(element?.textContent).toContain('Click Me');
  });

  it('should find multiple elements', () => {
    document.body.innerHTML = '<div class="item">1</div><div class="item">2</div>';

    const elements = elementSelector.findElements({
      selector: '.item',
    });

    expect(elements).toHaveLength(2);
  });

  it('should get element text', () => {
    document.body.innerHTML = '<div id="test">  Hello World  </div>';

    const element = document.getElementById('test');
    const text = elementSelector.getElementText(element!, true);

    expect(text).toBe('Hello World');
  });

  it('should check element visibility', () => {
    document.body.innerHTML = '<div id="visible">Visible</div>';

    const element = document.getElementById('visible');
    const isVisible = elementSelector.isElementVisible(element!);

    expect(isVisible).toBe(true);
  });

  it('should get element selector path', () => {
    document.body.innerHTML = '<div id="test">Content</div>';

    const element = document.getElementById('test');
    const selector = elementSelector.getElementSelector(element!);

    expect(selector).toContain('test');
  });

  it('should get clickable elements', () => {
    document.body.innerHTML = '<button>Button</button><a href="#">Link</a>';

    const clickable = elementSelector.getClickableElements();

    expect(clickable.length).toBeGreaterThan(0);
  });

  it('should get input elements', () => {
    document.body.innerHTML = '<input type="text"><textarea></textarea>';

    const inputs = elementSelector.getInputElements();

    expect(inputs).toHaveLength(2);
  });
});
