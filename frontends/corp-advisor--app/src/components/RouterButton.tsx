// src/components/Button.tsx
import React from "react";

type RouterButtonProps = {
  link: string;
  title: string;
  descriptiveText: React.ReactNode;
  isMobile: boolean;
  isTablet: boolean;
};

export function RouterButton({
  link,
  title,
  descriptiveText,
  isMobile,
  isTablet,
}: RouterButtonProps) {
  return (
    <a
      href={link}
      className="group my-3 px-4 py-3 bg-gray-100 rounded-lg hover:bg-gray-700 transition-transform transition-colors duration-200 transform hover:scale-105"
    >
      <h2
        className={`font-semibold mb-2 group-hover:text-gray-100 transition-colors duration-200
        font-semibold mb-2 group-hover:text-gray-100 transition-colors duration-200 ${
          isMobile ? "text-base" : isTablet ? "text-md" : "text-lg"
        }`}
      >
        {title}
      </h2>
      <h5 className="text-md text-gray-700 group-hover:text-gray-100 transition-colors duration-200">
        {descriptiveText}
      </h5>
    </a>
  );
}
