import { FinancialRecord } from "../hooks/useCsvData";

// ReportTable 컴포넌트가 받을 props의 타입을 정의합니다.
interface ReportTableProps {
  loading: boolean;
  error: string | null;
  data: FinancialRecord[];
  searchTerm: string;
  onSearchChange: (term: string) => void;
}

const ReportTable = ({
  loading,
  error,
  data,
  searchTerm,
  onSearchChange,
}: ReportTableProps) => {
  // 로딩 중일 때 표시할 UI
  if (loading) {
    return <div className="p-8 text-center">데이터를 불러오는 중입니다...</div>;
  }

  // 에러 발생 시 표시할 UI
  if (error) {
    return <div className="p-8 text-center text-red-500">오류: {error}</div>;
  }

  // 실제 UI를 렌더링하는 부분
  return (
    <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-md p-6">
      {/* 검색창 */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="기업명을 검색해주세요."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full md:w-1/3 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
        />
      </div>

      {/* 데이터 테이블 */}
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-4 border-b-2 border-gray-200 font-semibold text-gray-600">
                기업 코드
              </th>
              <th className="p-4 border-b-2 border-gray-200 font-semibold text-gray-600">
                기업 명
              </th>
              <th className="p-4 border-b-2 border-gray-200 font-semibold text-gray-600">
                기업 영문 명
              </th>
              <th className="p-4 border-b-2 border-gray-200 font-semibold text-gray-600">
                수정 일자
              </th>
            </tr>
          </thead>
          <tbody>
            {data.length > 0 ? (
              data.map((row, index) => (
                <tr
                  key={index}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="p-4 border-b border-gray-200 text-gray-700">
                    {row.corp_code}
                  </td>
                  <td className="p-4 border-b border-gray-200 text-gray-700">
                    {row.corp_name}
                  </td>
                  <td className="p-4 border-b border-gray-200 text-gray-700">
                    {row.corp_eng_name}
                  </td>
                  <td className="p-4 border-b border-gray-200 text-gray-700">
                    {row.modify_date}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="p-4 text-center text-gray-500">
                  검색 결과가 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ReportTable;
