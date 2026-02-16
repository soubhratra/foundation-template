"use client";

import type { ReactNode } from "react";

import { Switch } from "@/components/ui/switch";

interface PreferenceToggleProps {
  readonly label: string;
  readonly description?: string;
  readonly icon?: ReactNode;
  readonly checked: boolean;
  readonly onCheckedChange?: (value: boolean) => void;
  readonly disabled?: boolean;
}

export function PreferenceToggle({
  label,
  description,
  icon,
  checked,
  onCheckedChange,
  disabled,
}: PreferenceToggleProps) {
  return (
    <div className="flex items-center justify-between rounded-lg border px-3 py-2">
      <div className="flex items-center gap-3">
        {icon}
        <div>
          <p className="text-sm font-medium text-foreground">{label}</p>
          {description ? (
            <p className="text-xs text-muted-foreground">{description}</p>
          ) : null}
        </div>
      </div>
      <Switch
        checked={checked}
        onCheckedChange={onCheckedChange}
        disabled={disabled}
        aria-label={label}
      />
    </div>
  );
}
