import { useEffect, useId, useRef, type ReactNode } from "react";
export function ResearchDialog({
  name,
  onClose,
  children,
}: {
  name: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const host = useRef<HTMLElement>(null),
    close = useRef<HTMLButtonElement>(null),
    title = useId();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    close.current?.focus({ preventScroll: true });
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
      if (e.key === "Tab") {
        const nodes = [
          ...(host.current?.querySelectorAll<HTMLElement>(
            'button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex="0"]',
          ) || []),
        ].filter((n) => n.getClientRects().length);
        const first = nodes[0],
          last = nodes.at(-1);
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      document.body.style.overflow = overflow;
      if (previous?.isConnected) previous.focus({ preventScroll: true });
    };
  }, [onClose]);
  return (
    <div
      className="research-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        ref={host}
        className="research-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={title}
      >
        <header className="research-modal-head">
          <div>
            <span className="eyebrow">SECURITY RESEARCH</span>
            <h2 id={title}>{name} · 个股研究</h2>
          </div>
          <button
            ref={close}
            className="button"
            aria-label="关闭个股研究"
            onClick={onClose}
          >
            关闭 <kbd>Esc</kbd>
          </button>
        </header>
        <div className="research-modal-body">{children}</div>
      </section>
    </div>
  );
}
