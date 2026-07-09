import { useSelector, useDispatch } from "react-redux";
import { removeToast } from "../../features/toast/toastSlice";
import Toast from "./Toast";

const ToastContainer = () => {
  const toasts = useSelector((state) => state.toast.toasts);
  const dispatch = useDispatch();

  const handleClose = (id) => {
    dispatch(removeToast(id));
  };

  return (
    <div
      className="fixed bottom-4 left-4 z-[9999] flex flex-col gap-3 w-full max-w-sm pointer-events-none"
      aria-live="assertive"
      aria-instant="true"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto w-full">
          <Toast
            id={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={handleClose}
          />
        </div>
      ))}
    </div>
  );
};

export default ToastContainer;
