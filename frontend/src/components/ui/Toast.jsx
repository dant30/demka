import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const ToastContext = createContext(null);

const icons = {
  success: '✓',
  error: '!',
  warning: '!',
  info: 'i',
};

const styles = {
  success: 'border-green-200 bg-green-50 text-green-900',
  error: 'border-red-200 bg-red-50 text-red-900',
  warning: 'border-amber-200 bg-amber-50 text-amber-900',
  info: 'border-brand-200 bg-brand-50 text-brand-900',
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const notify = useCallback((message, options = {}) => {
    const id = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;
    const toast = {
      id,
      message,
      variant: options.variant ?? 'info',
      duration: options.duration ?? 4000,
    };
    setToasts((current) => [...current, toast]);

    if (toast.duration > 0) {
      window.setTimeout(() => dismiss(id), toast.duration);
    }
    return id;
  }, [dismiss]);

  const value = useMemo(() => ({
    notify,
    success: (message, options) => notify(message, { ...options, variant: 'success' }),
    error: (message, options) => notify(message, { ...options, variant: 'error' }),
    warning: (message, options) => notify(message, { ...options, variant: 'warning' }),
    info: (message, options) => notify(message, { ...options, variant: 'info' }),
    dismiss,
  }), [notify, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="fixed inset-x-3 bottom-[calc(var(--bottombar-height)+var(--safe-bottom)+0.75rem)] z-[var(--z-toast)] flex flex-col gap-2 md:bottom-5 md:left-auto md:w-[24rem]"
        aria-live="polite"
        aria-label="Notifications"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className={`flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg backdrop-blur-sm ${styles[toast.variant] ?? styles.info}`}
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-current/10 text-xs font-bold" aria-hidden="true">
              {icons[toast.variant] ?? icons.info}
            </span>
            <p className="min-w-0 flex-1 text-sm font-medium">{toast.message}</p>
            <button
              type="button"
              onClick={() => dismiss(toast.id)}
              className="-mr-1 h-6 w-6 rounded text-current/60 hover:bg-current/10 hover:text-current"
              aria-label="Dismiss notification"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

export default ToastProvider;
