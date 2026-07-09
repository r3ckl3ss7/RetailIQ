import { useEffect } from "react";

const Toast = ({ id, message, type = "error", onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, 5000);

    return () => clearTimeout(timer);
  }, [id, onClose]);

  return (
    <div
      className="animate-toast-in flex items-start gap-3 p-4 bg-slate-900/95 backdrop-blur-md border border-slate-800 border-l-4 border-l-red-500 rounded-lg shadow-xl shadow-slate-950/20 max-w-sm w-full transition-all duration-300"
      role="alert"
    >
      {/* Error Icon */}
      <div className="shrink-0 text-red-500 mt-0.5">
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>

      {/* Message Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-200">Error</p>
        <p className="text-xs text-slate-300 mt-0.5 break-words font-medium leading-relaxed">
          {message}
        </p>
      </div>

      {/* Close Button / Cross Mark */}
      <button
        onClick={() => onClose(id)}
        className="shrink-0 text-slate-400 hover:text-slate-200 transition-colors p-1 rounded hover:bg-slate-800/50"
        aria-label="Close notification"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
};

export default Toast;
