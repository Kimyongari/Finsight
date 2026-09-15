import "../App.css";
import { FileBarChart2, MessagesSquare, Sparkles } from "lucide-react";
import { RouterButton } from "../components/RouterButton";

const pipeline = [
  { label: "DART 전자공시", desc: "기업개황 · 재무제표 원문" },
  { label: "법령 벡터 검색", desc: "전자금융 법·규정 RAG" },
  { label: "웹 리서치", desc: "최신 뉴스 수집 · 요약" },
  { label: "LLM 분석", desc: "지표 해석 · 결론 생성" },
];

function Home() {
  return (
    <div className="flex min-h-screen w-full flex-col bg-ink-50">
      {/* 상단 바 */}
      <header className="border-b border-ink-200/80 bg-white/80 backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-5 py-3.5">
          <span className="text-[15px] font-extrabold tracking-tight text-ink-900">
            Fin<span className="text-brand-600">Sight</span>
          </span>
          <span className="hidden items-center gap-1.5 rounded-full border border-ink-200 bg-ink-50 px-3 py-1 text-[12px] font-medium text-ink-500 sm:inline-flex">
            <Sparkles size={13} className="text-brand-500" />
            AI 금융 분석 어시스턴트
          </span>
        </div>
      </header>

      {/* 히어로 */}
      <main className="mx-auto w-full max-w-5xl flex-1 px-5 pb-16 pt-14 sm:pt-20">
        <div className="mb-12 text-center sm:mb-14">
          <h1 className="mb-4 text-[40px] font-extrabold leading-[1.15] tracking-tight text-ink-900 sm:text-[52px]">
            Fin<span className="text-brand-600">Sight</span>
          </h1>
          <p className="mx-auto max-w-xl text-[16px] leading-relaxed text-ink-500 sm:text-[17px]">
            공시 · 법령 · 뉴스를 한 번에 읽어내는 금융 분석 에이전트.
            <br className="hidden sm:block" /> 기업 분석 보고서와 근거 기반
            법령 자문을 바로 받아보세요.
          </p>
        </div>

        {/* 기능 카드 */}
        <div className="grid grid-cols-1 gap-4 sm:gap-5 md:grid-cols-2">
          <RouterButton
            link="/report"
            icon={<FileBarChart2 size={22} />}
            title="기업 분석 보고서 생성"
            descriptiveText={
              <>
                기업명을 입력하면 DART 공시와 최신 뉴스를 모아 재무 지표 ·
                수익성 추이 · 종합 전망까지 담은 보고서를 자동으로 작성합니다.
              </>
            }
            tags={["DART 재무제표", "주가·수익성 차트", "뉴스 분석", "SWOT"]}
            ctaText="보고서 만들기"
          />
          <RouterButton
            link="/chatbot"
            icon={<MessagesSquare size={22} />}
            title="금융 자문 챗봇"
            descriptiveText={
              <>
                전자금융 관련 법령·감독규정을 벡터 검색으로 찾아 근거 조항과
                함께 답변합니다. 참조 조문 확장과 웹 검색도 선택할 수 있습니다.
              </>
            }
            tags={["법령 RAG", "참조 조문 확장", "웹 서치", "원문 PDF 확인"]}
            ctaText="질문하기"
          />
        </div>

        {/* 파이프라인 */}
        <section className="mt-14 sm:mt-16">
          <h2 className="mb-4 text-center text-[13px] font-semibold uppercase tracking-[0.12em] text-ink-400">
            데이터 파이프라인
          </h2>
          <ol className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {pipeline.map((step, index) => (
              <li
                key={step.label}
                className="rounded-xl border border-ink-200 bg-white p-4 shadow-card"
              >
                <span className="mb-2 inline-flex h-6 w-6 items-center justify-center rounded-md bg-ink-100 text-[12px] font-bold text-ink-500">
                  {index + 1}
                </span>
                <p className="text-[14px] font-semibold text-ink-800">
                  {step.label}
                </p>
                <p className="mt-0.5 text-[12.5px] leading-snug text-ink-500">
                  {step.desc}
                </p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="border-t border-ink-200/80 bg-white">
        <div className="mx-auto w-full max-w-5xl px-5 py-5 text-center text-[12.5px] text-ink-400">
          FinSight의 답변은 부정확할 수 있습니다. 투자 판단 전 원문 공시와 법령을
          직접 확인해주세요.
        </div>
      </footer>
    </div>
  );
}

export default Home;
