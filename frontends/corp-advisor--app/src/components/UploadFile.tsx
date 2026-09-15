import { FileText, X } from "lucide-react";

type uploadFileProp = {
  index: number;
  fileName: string;
  isLoading?: boolean;
  onDelete?: () => void;
};

export function UploadFile({
  index,
  fileName,
  isLoading,
  onDelete,
}: uploadFileProp) {
  return (
    <div
      key={index}
      className="flex items-center gap-2 rounded-lg bg-ink-50 px-2.5 py-2"
    >
      <FileText size={14} className="shrink-0 text-ink-400" />
      <span className="flex-1 truncate text-[13px] text-ink-700" title={fileName}>
        {fileName}
      </span>
      {!isLoading && onDelete && (
        <button
          type="button"
          onClick={onDelete}
          aria-label={`${fileName} 제거`}
          className="shrink-0 rounded p-1 text-ink-400 transition-colors hover:bg-red-50 hover:text-red-500"
        >
          <X size={13} />
        </button>
      )}
    </div>
  );
}
