import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface AsyncSelectOption {
  value: string;
  label: string;
}

export interface AsyncSelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  isError?: boolean;
  options?: AsyncSelectOption[];
  placeholder?: string;
  loadingMessage?: string;
  errorMessage?: string;
  emptyMessage?: string;
}

export function AsyncSelect({
  value,
  onValueChange,
  disabled,
  isLoading,
  isError,
  options,
  placeholder = "Selecione",
  loadingMessage = "Carregando...",
  errorMessage = "Erro ao carregar",
  emptyMessage = "Nenhum item encontrado",
}: AsyncSelectProps) {
  return (
    <Select
      value={value}
      onValueChange={onValueChange}
      disabled={disabled || isLoading || isError}
    >
      <SelectTrigger>
        <SelectValue
          placeholder={
            isLoading
              ? loadingMessage
              : isError
              ? errorMessage
              : !options || options.length === 0
              ? emptyMessage
              : placeholder
          }
        />
      </SelectTrigger>
      <SelectContent>
        {isError && (
          <SelectItem value="error" disabled>
            {errorMessage}
          </SelectItem>
        )}
        {!isLoading && !isError && (!options || options.length === 0) && (
          <SelectItem value="empty" disabled>
            {emptyMessage}
          </SelectItem>
        )}
        {options?.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
