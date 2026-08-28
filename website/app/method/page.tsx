import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Method",
  description:
    "The OWNED Method: Observe, Weigh, Navigate, Engineer, Demonstrate and transfer.",
};

const STEPS = [
  { title: "Observe", body: "Observe the real work." },
  { title: "Weigh", body: "Weigh value and risk." },
  { title: "Navigate", body: "Navigate the architecture." },
  { title: "Engineer", body: "Engineer controls and tests." },
  { title: "Demonstrate & transfer", body: "Demonstrate performance, train the team, and transfer ownership." },
];

export default function MethodPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/method", label: "Method" }]} />
        <h1>Start with the process, not the model.</h1>
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
