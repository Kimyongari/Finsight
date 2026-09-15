// src/components/Button.tsx
import React from "react";

type ButtonProps = {
  ButtonText: string;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
  variant?: "primary" | "ghost";
  disabled?: boolean;
};

export function Button({
  ButtonText,
  onClick,
  variant = "primary",
  disabled = false,
}: ButtonProps) {
  const base =
    "inline-flex w-full items-center justify-center rounded-xl px-4 py-2.5 text-[14px] font-semibold transition-all duration-150 disabled:pointer-events-none disabled:opacity-50";
  const styles =
    variant === "primary"
      ? "bg-brand-600 text-white hover:bg-brand-700 active:scale-[0.98]"
      : "border border-ink-200 bg-white text-ink-600 hover:bg-ink-50 hover:text-ink-900";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${styles}`}
    >
      {ButtonText}
    </button>
  );
}
