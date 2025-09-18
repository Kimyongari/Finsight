// components/steps/Step3_Complete.tsx
type Props = {
  onClose: () => void; // 모달 닫기 함수
};

export function CompleteModal({ onClose }: Props) {
  return (
    <div className="text-center">
      <h2 className="text-xl font-bold mb-4">✅ 완료</h2>
      <p className="mb-4">모든 작업이 성공적으로 완료되었습니다.</p>
      <button
        onClick={onClose}
        className="w-full bg-gray-500 text-white py-2 px-4 rounded"
      >
        닫기
      </button>
    </div>
  );
}
