/**
 * Assistant type definitions.
 */

export interface Assistant {
  id: string;
  name: string;
  instructions: string;
  model: string;
  status: "active" | "inactive" | "deleted";
  created_at: string;
  updated_at: string;
  last_active_at?: string;
  capabilities: string[];
}

export interface CreateAssistantRequest {
  name: string;
  instructions: string;
  model?: string;
  capabilities: string[];
}

export interface Capability {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: "navigation" | "interaction" | "extraction" | "utility";
  risk_level: "low" | "medium" | "high";
  enabled: boolean;
}
