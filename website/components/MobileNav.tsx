"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PRIMARY_NAV } from "@/lib/nav";

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const panelRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);

  // Close the menu on navigation. Derived during render (not an effect) per
  // https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes
  const [priorPathname, setPriorPathname] = useState(pathname);
  if (pathname !== priorPathname) {
    setPriorPathname(pathname);
    if (open) setOpen(false);
  }

  useEffect(() => {
    if (!open) return;

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
        toggleRef.current?.focus();
        return;
      }
      if (e.key !== "Tab" || !panelRef.current) return;
      const focusable = panelRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled])'
      );
      if (focusable.length === 0) return;
      const first = focusable[0]!;
      const last = focusable[focusable.length - 1]!;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    const firstLink = panelRef.current?.querySelector<HTMLElement>("a[href]");
    firstLink?.focus();
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open]);

  return (
    <>
      <button
        ref={toggleRef}
        type="button"
        className="nav-toggle"
        aria-expanded={open}
        aria-controls="mobile-nav-panel"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "Close menu" : "Menu"}
      </button>
      {open && (
        <div
          id="mobile-nav-panel"
          className="mobile-nav"
          ref={panelRef}
          role="dialog"
          aria-modal="true"
          aria-label="Site navigation"
        >
          <ul>
            {PRIMARY_NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={pathname === item.href ? "page" : undefined}
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/contact" className="btn btn-primary">
                Book a fit call
              </Link>
            </li>
          </ul>
        </div>
      )}
    </>
  );
}
