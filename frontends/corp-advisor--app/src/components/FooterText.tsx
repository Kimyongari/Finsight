type FooterTextProps = {
  footerText: string;
};

export function FooterText({ footerText }: FooterTextProps) {
  return (
    <p className="text-center text-[11.5px] leading-relaxed text-ink-400">
      {footerText}
    </p>
  );
}
