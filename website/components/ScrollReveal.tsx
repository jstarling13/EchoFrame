"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

/**
 * Fades/rises a section into place the first time it scrolls into view.
 * Client-only by necessity (IntersectionObserver), but degrades safely:
 * server-rendered HTML already has the content in place (this only ever
 * adds a class, never conditionally renders), so nothing depends on JS
 * for the content itself to exist — only for the entrance animation.
 */
export default function ScrollReveal({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={`scroll-reveal${visible ? " is-visible" : ""}${className ? ` ${className}` : ""}`}>
      {children}
    </div>
  );
}
