/**
 * Content script entry point.
 * Handles tool execution requests from background script.
 */

import { domController } from "./dom-controller";

console.log("BrowserMind content script loaded");

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("Content script received message:", message.type);

  // Handle async tool execution
  (async () => {
    try {
      if (message.type === "execute_tool") {
        const { tool, params } = message;

        // Execute tool using DOM controller
        let result;
        switch (tool) {
          case "navigate":
            result = await domController.navigate(params);
            break;
          case "click_element":
            result = await domController.clickElement(params);
            break;
          case "type_text":
            result = await domController.typeText(params);
            break;
          case "scroll":
            result = await domController.scroll(params);
            break;
          case "extract_text":
            result = await domController.extractText(params);
            break;
          case "extract_links":
            result = await domController.extractLinks(params);
            break;
          case "extract_tables":
            result = await domController.extractLinks(params); // Placeholder
            break;
          case "get_dom":
            result = await domController.getDOM(params);
            break;
          case "highlight_element":
            result = await domController.highlightElement(params);
            break;
          case "screenshot":
            // Screenshot must be handled by background script
            sendResponse({
              success: false,
              error: "Screenshot must be handled by background script",
            });
            return;
          default:
            throw new Error(`Unknown tool: ${tool}`);
        }

        // Send success response
        sendResponse({
          success: true,
          result: result,
        });
      } else {
        sendResponse({
          success: false,
          error: "Unknown message type",
        });
      }
    } catch (error) {
      console.error("Error executing tool:", error);
      sendResponse({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      });
    }
  })();

  // Return true to indicate async response
  return true;
});

// Notify background script that content script is ready
chrome.runtime.sendMessage({
  type: "content_script_ready",
  url: window.location.href,
});
