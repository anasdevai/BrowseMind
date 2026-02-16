/**
 * Status indicator component for connection and execution status.
 */

import React from "react";
import { Badge } from "../components/ui/badge";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import type { ConnectionStatus } from "../types/websocket";

interface StatusIndicatorProps {
  status: ConnectionStatus;
}

export function StatusIndicator({ status }: StatusIndicatorProps) {
  const getStatusConfig = () => {
    switch (status) {
      case "connected":
        return {
          icon: <Wifi className="h-3 w-3" />,
          label: "Connected",
          variant: "default" as const,
        };
      case "connecting":
        return {
          icon: <Loader2 className="h-3 w-3 animate-spin" />,
          label: "Connecting",
          variant: "secondary" as const,
        };
      case "disconnected":
        return {
          icon: <WifiOff className="h-3 w-3" />,
          label: "Disconnected",
          variant: "destructive" as const,
        };
      case "error":
        return {
          icon: <WifiOff className="h-3 w-3" />,
          label: "Error",
          variant: "destructive" as const,
        };
      default:
        return {
          icon: <WifiOff className="h-3 w-3" />,
          label: "Unknown",
          variant: "secondary" as const,
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      {config.icon}
      <span className="text-xs">{config.label}</span>
    </Badge>
  );
}
