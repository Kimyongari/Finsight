type LoadingSpinnerProps = {
  loadingText: string;
};

export const LoadingSpinner = ({loadingText} : LoadingSpinnerProps) => (<div className="flex justify-center items-center py-2">
  <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
  <span className="ml-6">{loadingText}</span>
</div>);
