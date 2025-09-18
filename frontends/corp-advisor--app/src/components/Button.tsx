// src/components/Button.tsx
import React from "react";

type ButtonProps = {
  ButtonText: string;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
};

export function Button({ ButtonText, onClick }: ButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="px-4 py-2 border border-gray-300 text-gray-600 text-sm font-bold rounded-lg hover:bg-gray-100 hover:text-black transition-colors duration-200"
    >
      {ButtonText}
    </button>
  );
}
