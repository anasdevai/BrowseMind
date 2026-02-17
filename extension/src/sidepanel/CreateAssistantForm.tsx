/**
 * Create Assistant Form Component
 * Form for creating new assistants with capability selection
 */

import React, { useState } from "react";
import { useBrowserMindStore } from "~/lib/store";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Card } from "~/components/ui/card";
import { CapabilitySelector } from "./CapabilitySelector";

const AVAILABLE_CAPABILITIES = [
  { name: "navigate", description: "Navigate to URLs" },
  { name: "click_element", description: "Click elements on page" },
  { name: "type_text", description: "Type text into inputs" },
  { name: "scroll", description: "Scroll page" },
  { name: "screenshot", description: "Capture screenshots" },
  { name: "extract_text", description: "Extract text from elements" },
  { name: "extract_links", description: "Extract links from page" },
  { name: "extract_tables", description: "Extract table data" },
  { name: "get_dom", description: "Get DOM structure" },
  { name: "highlight_element", description: "Highlight elements" },
];

export function CreateAssistantForm({ onClose }: { onClose: () => void }) {
  const { connectionStatus } = useBrowserMindStore();
  const [name, setName] = useState("");
  const [instructions, setInstructions] = useState("");
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      alert("Please enter an assistant name");
      return;
    }

    if (selectedCapabilities.length === 0) {
      alert("Please select at least one capability");
      return;
    }

    if (selectedCapabilities.length > 10) {
      alert("Maximum 10 capabilities allowed");
      return;
    }

    setIsSubmitting(true);

    try {
      // Send create_assistant message
      await chrome.runtime.sendMessage({
        type: "send_command",
        payload: {
          type: "create_assistant",
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          payload: {
            name: name.trim(),
            instructions: instructions.trim(),
            capabilities: selectedCapabilities,
          },
        },
      });

      // Reset form
      setName("");
      setInstructions("");
      setSelectedCapabilities([]);
      onClose();
    } catch (error) {
      console.error("Error creating assistant:", error);
      alert("Failed to create assistant");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="p-4">
      <h2 className="text-lg font-semibold mb-4">Create New Assistant</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Name</label>
          <Input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Assistant"
            maxLength={50}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Instructions (Optional)
          </label>
          <textarea
            className="w-full min-h-[80px] px-3 py-2 text-sm border rounded-md"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Custom instructions for this assistant..."
            maxLength={500}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Capabilities (Max 10)
          </label>
          <CapabilitySelector
            capabilities={AVAILABLE_CAPABILITIES}
            selected={selectedCapabilities}
            onChange={setSelectedCapabilities}
          />
        </div>

        <div className="flex gap-2">
          <Button
            type="submit"
            disabled={connectionStatus !== "connected" || isSubmitting}
          >
            {isSubmitting ? "Creating..." : "Create Assistant"}
          </Button>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
}
