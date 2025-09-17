import React from "react";

type FooterTextProps = {
  footerText: string;
};

export function FooterText({ footerText }: FooterTextProps) {
  return <div className="text-center text-xs text-gray-400">{footerText}</div>;
}
