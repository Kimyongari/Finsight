import React, {useState, useRef, useEffect} from "react";

const options = ["간단 RAG", "심화 RAG", "RAG 3번"];

export function RagDropdown({onSelect} : {
  onSelect: (value : string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [selected, setSelected] = useState < string | null > (null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 바깥 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event : MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return() => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (option : string) => {
    setSelected(option);
    setIsOpen(false);
    onSelect(option);
  };

  return (<div ref={dropdownRef} className="relative w-40">
    <button onClick={() => setIsOpen((prev) => !prev)} className="w-full p-2 border rounded bg-white text-left">
      {selected || "RAG 선택"}
    </button>

    {
      isOpen && (<ul className="absolute w-full bg-white border rounded mt-1 shadow-lg z-10">
        {
          options.map((option) => (<li key={option} className="p-2 hover:bg-indigo-100 cursor-pointer" onClick={() => handleSelect(option)}>
            {option}
          </li>))
        }
      </ul>)
    }
  </div>);
}
