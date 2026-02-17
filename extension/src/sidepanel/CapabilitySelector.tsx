/**
 * Capability Selector Component
 * Checkbox list for selecting assistant capabilities with max 10 validation
 */

import React from "react";

interface Capability {
  name: string;
  description: string;
}

interface CapabilitySelectorProps {
  capabilities: Capability[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

export function CapabilitySelector({
  capabilities,
  selected,
  onChange,
}: CapabilitySelectorProps) {
  const handleToggle = (capabilityName: string) => {
    if (selected.includes(capabilityName)) {
      // Remove capability
      onChange(selected.filter((name) => name !== capabilityName));
    } else {
      // Add capability (max 10)
      if (selected.length >= 10) {
        alert("Maximum 10 capabilities allowed");
        return;
      }
      onChange([...selected, capabilityName]);
    }
  };

  return (
    <div className="space-y-2 max-h-[300px] overflow-y-auto border rounded-md p-3">
      {capabilities.map((capability) => (
        <label
          key={capability.name}
          className="flex items-start gap-2 cursor-pointer hover:bg-accent p-2 rounded"
        >
          <input
            type="checkbox"
            checked={selected.includes(capability.name)}
            onChange={() => handleToggle(capability.name)}
            className="mt-1"
          />
          <div className="flex-1">
            <div className="font-medium text-sm">{capability.name}</div>
            <div className="text-xs text-muted-foreground">
              {capability.description}
            </div>
          </div>
        </label>
      ))}

      <div className="text-xs text-muted-foreground pt-2 border-t">
        {selected.length} / 10 capabilities selected
      </div>
    </div>
  );
}
