import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

type RouterButtonProps = {
  link: string;
  title: string;
  descriptiveText: React.ReactNode;
  /** 카드 좌측 상단 아이콘 */
  icon: React.ReactNode;
  /** 기능 요약 배지 */
  tags?: string[];
  /** 카드 하단 CTA 문구 */
  ctaText?: string;
};

export function RouterButton({
  link,
  title,
  descriptiveText,
  icon,
  tags = [],
  ctaText = "시작하기",
}: RouterButtonProps) {
  return (
    <Link
      to={link}
      className="group flex h-full flex-col rounded-2xl border border-ink-200 bg-white p-6 text-left shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-lift focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 sm:p-7"
    >
      <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600 transition-colors duration-200 group-hover:bg-brand-600 group-hover:text-white">
        {icon}
      </div>

      <h2 className="mb-2 text-lg font-bold tracking-tight text-ink-900">
        {title}
      </h2>
      <p className="mb-5 text-[14px] leading-relaxed text-ink-500">
        {descriptiveText}
      </p>

      {tags.length > 0 && (
        <ul className="mb-6 flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <li
              key={tag}
              className="rounded-full border border-ink-200 bg-ink-50 px-2.5 py-1 text-[12px] font-medium text-ink-600"
            >
              {tag}
            </li>
          ))}
        </ul>
      )}

      <span className="mt-auto inline-flex items-center gap-1.5 text-[14px] font-semibold text-brand-600">
        {ctaText}
        <ArrowRight
          size={16}
          className="transition-transform duration-200 group-hover:translate-x-1"
        />
      </span>
    </Link>
  );
}
