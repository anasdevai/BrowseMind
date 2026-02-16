/**
 * Content script entry point.
 * Handles tool execution requests from background script.
 */

import type { PlasmoCSConfig } from "plasmo";
import { domController } from "./dom-controller";

export const config: PlasmoCSConfig = {
  matches: ["<all_urls>"],
  all_frames: false,
};

// Message types from background script
interface ToolExecutionMessage {
  type: "execute_tool";
  tool: string;
  params: Record<string, any>;
  messageId: string;
}

interface ToolResultMessage {
  type: "tool_result";
  messageId: string;
  success: boolean;
  result?: any;
  error?: string;
}

/**
 * Execute a tool command.
 */
async function executeTool(
  tool: string,
  params: Record<string, any>
): Promise<any> {
  switch (tool) {
    case "navigate":
      return await domController.navigate(params);
    case "click_element":
      return await domController.clickElement(params);
    case "type_text":
      return await domController.typeText(params);
    case "scroll":
      return await domController.scroll(params);
    case "extract_text":
      return await domController.extractText(params);
    case "extract_links":
      return await domController.extractLinks(params);
    case "get_dom":
      return await domController.getDOM(params);
    case "highlight_element":
      return await domController.highlightElement(params);
    case "screenshot":
      // Screenshot is handled by background script
      throw new Error("Screenshot must be handled by background script");
    default:
      throw new Error(`Unknown tool: ${tool}`);
  }
}

/**
 * Handle messages from background script.
 */
chrome.runtime.onMessage.addListener(
  (
    message: ToolExecutionMessage,
    sender: chrome.runtime.MessageSender,
    sendResponse: (response: ToolResultMessage) => void
  ) => {
    if (message.type === "execute_tool") {
      // Execute tool asynchronously
      executeTool(message.tool, message.params)
        .then((result) => {
          sendResponse({
            type: "tool_result",
            messageId: message.messageId,
            success: true,
            result,
          });
        })
        .catch((error) => {
          console.error(`Tool execution error (${message.tool}):`, error);
          sendResponse({
            type: "tool_result",
            messageId: message.messageId,
            success: false,
            error: error.message || String(error),
          });
        });

      // Return true to indicate async response
      return true;
    }
  }
);

console.log("BrowserMind content script loaded");
