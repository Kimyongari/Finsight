import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from "react";
const messages = [
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    {
        type: "answer",
        text: "삼성전자 보고서를 생성 중입니다...삼성전자의 경우 2023년도 매출에 비해 2024년도 매출이 크게 올랐습니다. 이는 반도체 사업의 부진을 스마트폰, 가전제품과 같은 영역을 통해 극복한 모습으로 볼 수 있습니다. 다만 어닝 쇼크가 있었던 만큼 투자 심리에 악역향을 끼쳤습니다. 현재는 코스피 지수가 3000대를 돌파한 후 70000원대의 주가를 보이며 앞으로도 상승세를 그릴 것으로 예상됩니다.",
    },
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    { type: "answer", text: "삼성전자 보고서를 생성 중입니다..." },
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    { type: "answer", text: "삼성전자 보고서를 생성 중입니다..." },
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    { type: "answer", text: "삼성전자 보고서를 생성 중입니다..." },
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    { type: "answer", text: "삼성전자 보고서를 생성 중입니다..." },
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    { type: "answer", text: "삼성전자 보고서를 생성 중입니다..." },
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    { type: "answer", text: "삼성전자 보고서를 생성 중입니다..." },
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    { type: "answer", text: "삼성전자 보고서를 생성 중입니다..." },
    { type: "question", text: "삼성전자 보고서를 생성해주세요." },
    { type: "answer", text: "삼성전자 보고서를 생성 중입니다..." },
];
function Report() {
    const [inputValue, setInputValue] = useState("");
    const handleSubmit = () => {
        if (inputValue.trim()) {
            console.log("생성 요청:", inputValue);
            setInputValue("");
        }
    };
    const handleKeyPress = (e) => {
        if (e.key === "Enter") {
            handleSubmit();
        }
    };
    const hasMessages = messages.length > 0;
    // 입력 창의 내부 컨텐츠를 상수로 분리 (코드 중복 방지)
    const FormContent = (_jsxs(_Fragment, { children: [_jsxs("div", { className: "flex gap-2 mb-2", children: [_jsx("input", { type: "text", value: inputValue, onChange: (e) => setInputValue(e.target.value), onKeyPress: (e) => handleKeyPress(e), placeholder: "\uBCF4\uACE0\uC11C \uC0DD\uC131\uC744 \uC6D0\uD558\uC2DC\uB294 \uAE30\uC5C5\uBA85\uC744 \uC791\uC131\uD574\uC8FC\uC138\uC694.", className: "flex-1 p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500" }), _jsx("button", { type: "button", onClick: handleSubmit, className: "px-6 py-3 bg-indigo-500 text-white rounded hover:bg-indigo-600 transform transition-transform duration-300 hover:scale-105", children: "\u2B06" })] }), _jsx("div", { className: "text-center text-sm text-gray-500", children: "CorpAdvisor\uC758 \uB2F5\uBCC0\uC5D0\uC11C \uC2E4\uC218\uAC00 \uBC1C\uC0DD\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4. \uC911\uC694\uD55C \uC815\uBCF4\uB294 \uD55C \uBC88 \uB354 \uD655\uC778\uD574\uC8FC\uC138\uC694." })] }));
    return (_jsx("div", { className: "min-h-screen", children: hasMessages ? (
        // --- 메시지가 있을 때 ---
        _jsxs(_Fragment, { children: [_jsx("div", { className: "w-1/2 mx-auto flex flex-col gap-3 mb-6 p-4 pb-32", children: messages.map((msg, idx) => (_jsx("div", { className: `p-3 rounded-xl break-words ${msg.type === "question"
                            ? "self-end bg-gray-100 text-gray-700 rounded-tr-none"
                            : "text-gray-700"}`, children: msg.text }, idx))) }), _jsx("div", { className: "bg-white border-t border-gray-200 p-4 fixed bottom-0 left-0 right-0", children: _jsx("div", { className: "w-1/2 mx-auto", children: FormContent }) })] })) : (
        // --- 메시지가 없을 때 ---
        _jsxs("div", { className: "flex flex-col justify-center items-center min-h-screen gap-6", children: [_jsx("header", { className: "py-6", children: _jsx("h1", { className: "text-3xl font-bold text-center", children: "\uAE30\uC5C5 \uBCF4\uACE0\uC11C \uC0DD\uC131" }) }), _jsx("div", { className: "bg-white p-4", children: FormContent })] })) }));
}
export default Report;
