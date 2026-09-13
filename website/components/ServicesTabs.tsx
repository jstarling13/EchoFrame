"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { SERVICE_CAPABILITIES } from "@/lib/services";
import ServicesGrid from "./ServicesGrid";
import PricingModel from "./PricingModel";
import EngagementJourney from "./EngagementJourney";
import Faq from "./Faq";

/**
 * Capabilities is the default tab, and every external link into this page
 * (footer nav, /training, /insights) targets a service-card #id that only
 * exists inside ServicesGrid. That's enough for a first page load, but a
 * hash-only URL change (e.g. clicking a footer service link while already
 * sitting on /services, on the Pricing tab) never reloads the page — the
 * browser just updates the hash and tries to scroll, with no help from
 * React state. The effect below listens for that and switches back to
 * Capabilities whenever the hash names a real service slug, on mount and
 * on every subsequent hash change.
 */
const SERVICE_SLUGS = new Set(SERVICE_CAPABILITIES.map((s) => s.slug));

const TABS = [
  { id: "capabilities", label: "Capabilities" },
  { id: "pricing", label: "Pricing" },
  { id: "process", label: "How It Works" },
  { id: "faq", label: "FAQ" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function ServicesTabs() {
  const baseId = useId();
  const [active, setActive] = useState<TabId>("capabilities");
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  useEffect(() => {
    function syncToHash() {
      const slug = window.location.hash.slice(1);
      if (slug && SERVICE_SLUGS.has(slug)) {
        setActive("capabilities");
        // The element was hidden when the browser first tried to scroll
        // to it (or didn't exist yet on initial mount) — now that its
        // panel is visible, finish the job manually.
        requestAnimationFrame(() => {
          document.getElementById(slug)?.scrollIntoView();
        });
      }
    }
    syncToHash();
    window.addEventListener("hashchange", syncToHash);
    return () => window.removeEventListener("hashchange", syncToHash);
  }, []);

  function focusTab(index: number) {
    const wrapped = (index + TABS.length) % TABS.length;
    const tab = TABS[wrapped]!;
    setActive(tab.id);
    tabRefs.current[wrapped]?.focus();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    switch (event.key) {
      case "ArrowRight":
        event.preventDefault();
        focusTab(index + 1);
        break;
      case "ArrowLeft":
        event.preventDefault();
        focusTab(index - 1);
        break;
      case "Home":
        event.preventDefault();
        focusTab(0);
        break;
      case "End":
        event.preventDefault();
        focusTab(TABS.length - 1);
        break;
    }
  }

  return (
    <div className="services-tabs">
      <div role="tablist" aria-label="Services sections" className="services-tabs__list">
        {TABS.map((tab, index) => (
          <button
            key={tab.id}
            ref={(el) => {
              tabRefs.current[index] = el;
            }}
            type="button"
            role="tab"
            id={`${baseId}-tab-${tab.id}`}
            aria-selected={active === tab.id}
            aria-controls={`${baseId}-panel-${tab.id}`}
            tabIndex={active === tab.id ? 0 : -1}
            className={`services-tabs__tab${active === tab.id ? " is-active" : ""}`}
            onClick={() => setActive(tab.id)}
            onKeyDown={(event) => handleKeyDown(event, index)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div
        role="tabpanel"
        id={`${baseId}-panel-capabilities`}
        aria-labelledby={`${baseId}-tab-capabilities`}
        hidden={active !== "capabilities"}
      >
        <ServicesGrid />
      </div>
      <div
        role="tabpanel"
        id={`${baseId}-panel-pricing`}
        aria-labelledby={`${baseId}-tab-pricing`}
        hidden={active !== "pricing"}
      >
        <h2>How Engagement Works</h2>
        <PricingModel />
      </div>
      <div
        role="tabpanel"
        id={`${baseId}-panel-process`}
        aria-labelledby={`${baseId}-tab-process`}
        hidden={active !== "process"}
      >
        <EngagementJourney />
      </div>
      <div
        role="tabpanel"
        id={`${baseId}-panel-faq`}
        aria-labelledby={`${baseId}-tab-faq`}
        hidden={active !== "faq"}
      >
        <h2>Frequently asked questions</h2>
        <Faq />
      </div>
    </div>
  );
}
