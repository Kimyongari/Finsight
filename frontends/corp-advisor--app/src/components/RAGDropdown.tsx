import React, { useState, useRef, useEffect } from "react";
import { QueryMode } from "../hooks/useDynamicQuery"; // QueryMode 타입을 가져옵니다.

// 옵션을 객체 배열로 변경 (label: 화면 표시용, value: 내부 로직용)
const options: { label: string; value: QueryMode }[] = [
  { label: "일반 분석", value: "rag" },
  { label: "심층 분석", value: "advanced_rag" },
  { label: "웹 서치", value: "web_search" },
];

type RAGDropdownProps = {
  // onSelect가 QueryMode 타입을 받도록 수정
  onSelect: (value: QueryMode) => void;
  hasMessages: boolean;
};

export function RAGDropdown({ onSelect, hasMessages }: RAGDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  // 선택된 옵션 객체 전체를 저장하거나, label만 저장
  const [selectedLabel, setSelectedLabel] = useState<string>("일반 분석");
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (option: { label: string; value: QueryMode }) => {
    setSelectedLabel(option.label); // 화면에는 label 표시
    setIsOpen(false);
    onSelect(option.value); // 부모에게는 value(영문 key) 전달
  };

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-40 p-3 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition resize-none overflow-y-hidden border-none"
      >
        {selectedLabel}
      </button>

      {isOpen && (
        <ul
          className={`${
            hasMessages ? "bottom-full mb-2" : "top-full mt-2"
          } absolute bg-white border rounded mt-1 shadow-lg z-10 w-40 text-center`}
        >
          {options.map((option) => (
            <li
              key={option.value}
              className="p-2 hover:bg-indigo-100 cursor-pointer"
              onClick={() => handleSelect(option)}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
