/**
 * EchoFrame bills hourly, quoted per project — not a self-serve product.
 * There is deliberately no public "buy now" button anywhere on this site.
 * This component states the actual client journey everywhere pricing is
 * shown, so nothing implies instant self-serve purchase.
 */
const STEPS = [
  { title: "Free discovery call", body: "A focused 20-30 minute conversation to confirm the workflow is real and automation is the right answer — no charge, no obligation." },
  { title: "Paid diagnostic (when needed)", body: "Complex or multi-system workflows get mapped properly first, billed at the standard hourly rate — simple, well-understood work skips straight to a quote." },
  { title: "Written quote", body: "A scoped estimate at the standard hourly rate, plus travel fee and food stipend if the work is onsite." },
  { title: "Agreement", body: "Scope and terms are confirmed in writing before work begins." },
  { title: "Kickoff", body: "Work starts on the agreed date; hours are billed as they're actually worked." },
  { title: "Invoice", body: "Invoiced for hours worked plus any travel and stipend — never charged upfront through a public checkout." },
];

export default function EngagementJourney() {
  return (
    <div>
      <h2>How an engagement starts</h2>
      <p>
        Every engagement is scoped to your business, not a self-serve
        purchase. No price on this site can be paid by clicking a public
        button.
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
  );
}
