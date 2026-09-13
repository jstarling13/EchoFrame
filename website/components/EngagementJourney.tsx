/**
 * EchoFrame bills hourly, quoted per project — not a self-serve product.
 * There is deliberately no public "buy now" button anywhere on this site.
 * Sits directly below PricingModel on /services, so this only covers
 * what happens AFTER pricing is understood (quote → agreement → kickoff
 * → invoice) — it doesn't restate the free call, paid-diagnostic
 * threshold, or travel/stipend figures, since PricingModel already
 * states those and repeating them read as padding.
 */
const STEPS = [
  { title: "Written quote", body: "A scoped estimate confirming the hours, plus travel and stipend if the work is onsite, before anything begins." },
  { title: "Agreement", body: "Scope and terms are confirmed in writing before work begins." },
  { title: "Kickoff", body: "Work starts on the agreed date; hours are billed as they're actually worked." },
  { title: "Invoice", body: "Invoiced for hours worked plus any travel and stipend." },
];

export default function EngagementJourney() {
  return (
    <div>
      <h2>What happens after the quote</h2>
      <ol className="steps">
        {STEPS.map((step) => (
          <li key={step.title}>
            <h3>{step.title}</h3>
            <p>{step.body}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
