/**
 * White Oak Operations sells scoped professional services, not a
 * self-serve product. There is deliberately no public "buy now" button
 * for O1-O5 anywhere on this site — see
 * website/docs/NO_PUBLIC_CHECKOUT.md for the full rationale. This
 * component states the actual approved client journey everywhere pricing
 * is shown, so nothing implies instant self-serve purchase.
 */
const STEPS = [
  { title: "Fit call", body: "A short call to confirm this is the right engagement." },
  { title: "Qualification", body: "We confirm scope, workflow, and constraints fit an offer." },
  { title: "Proposal", body: "A written proposal scoped to your workflow and offer code." },
  { title: "Signed MSA/SOW", body: "Contract terms and scope are agreed and signed." },
  {
    title: "Private deposit invoice or payment link",
    body: "We send a private Stripe invoice or payment link — never a public checkout button.",
  },
  { title: "Kickoff", body: "Work begins once the deposit is received." },
];

export default function EngagementJourney() {
  return (
    <div>
      <h2>How an engagement starts</h2>
      <p>
        Every engagement is a scoped professional service, not a
        self-serve purchase. No price on this site can be paid by clicking
        a public button.
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
