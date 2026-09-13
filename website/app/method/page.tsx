import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Method",
  description:
    "The OWNED Method™: EchoFrame's proprietary five-stage framework — Observe, Weigh, Navigate, Engineer, Demonstrate and transfer.",
};

const STEPS = [
  { title: "Observe", body: "Observe the real work, not the org chart's version of it." },
  { title: "Weigh", body: "Weigh value against risk before a single workflow is touched." },
  { title: "Navigate", body: "Navigate the architecture — vendor-neutral, evidence-led, never brand-first." },
  { title: "Engineer", body: "Engineer the controls, tests, and fallbacks into the build itself." },
  { title: "Demonstrate & Transfer", body: "Demonstrate measurable performance, train the team, and transfer full ownership." },
];

export default function MethodPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/method", label: "Method" }]} />
        <p className="eyebrow">The Case for Process Before Platform</p>
        <h1>The OWNED Method&trade;</h1>
        <p>
          Most automation initiatives fail before the first model is ever
          chosen &mdash; not from bad AI, but from skipping the discipline of
          understanding the process underneath it. The OWNED Method&trade;
          is EchoFrame&rsquo;s proprietary framework for closing that gap:
          five deliberate moves from diagnosis to full ownership transfer,
          engineered for measurable risk reduction at every stage.
        </p>
        <ol className="steps">
          {STEPS.map((step) => (
            <li key={step.title}>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </main>
  );
}
