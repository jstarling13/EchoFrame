import { PRICING_LINE_ITEMS } from "@/lib/services";

export default function PricingModel() {
  return (
    <div className="offers-table-wrap">
      <table className="offers">
        <caption>How pricing works — one simple rate, quoted per project.</caption>
        <thead>
          <tr>
            <th scope="col">What</th>
            <th scope="col">How it's billed</th>
          </tr>
        </thead>
        <tbody>
          {PRICING_LINE_ITEMS.map((item) => (
            <tr key={item.label}>
              <td>{item.label}</td>
              <td>{item.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="hint" style={{ marginTop: "1rem" }}>
        No fixed packages, no public checkout. Every project gets a written
        quote after a short conversation about the actual problem, scoped to
        the hours it will realistically take.
      </p>
    </div>
  );
}
