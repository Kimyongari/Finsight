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
    <div key={index} className="flex items-center mb-2">
      <span className="flex-1">{fileName}</span>
      {!isLoading && onDelete && (
        <button
          onClick={onDelete}
          className="ml-2 bg-red-500 text-white px-2 py-1 rounded"
        >
          X
        </button>
      )}
    </div>
  );
}
