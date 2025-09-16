import "../App.css";
import { useMediaQuery } from "react-responsive";
import { RouterButton } from "../components/RouterButton";

function Home() {
  const isMobile = useMediaQuery({
    maxWidth: 768,
    ssrMatchMedia: () => ({ matches: false }),
  } as any);

  const isTablet = useMediaQuery({
    minWidth: 769,
    maxWidth: 1224,
    ssrMatchMedia: () => ({ matches: false }),
  } as any);

  return (
    <div className="p-12 flex flex-col justify-center align-center text-center">
      <h1 className="text-5xl font-bold mb-5">
        Fin<span className="text-indigo-700">Sight</span>
      </h1>
      <div className="intro p-6">
        <h5 className="text-md text-gray-700 leading-relaxed">
          기업과 금융의 인사이트를 발견해보세요.
        </h5>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <RouterButton
          link="/report"
          isMobile={isMobile}
          isTablet={isTablet}
          title="기업 분석 보고서 생성"
          descriptiveText={
            <>
              기업 소개, 재무 분석, 성장 가능성을 담은 <br />
              종합 분석 보고서를 생성할 수 있어요.
            </>
          }
        />
        <RouterButton
          link="/chatbot"
          isMobile={isMobile}
          isTablet={isTablet}
          title="금융 자문 챗봇"
          descriptiveText={
            <>
              금융과 관련된 법적 질의와
              <br />
              전문적인 자문을 받을 수 있어요.
            </>
          }
        />
      </div>
    </div>
  );
}

export default Home;
