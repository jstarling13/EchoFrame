interface Step {
  title: string;
  body: string;
}

export default function MethodFlow({ steps }: { steps: Step[] }) {
  return (
    <div className="method-flow">
      {steps.map((step, i) => (
        <div className="method-flow-item" key={step.title}>
          <div className="method-flow-card">
            <span className="method-flow-number">{i + 1}</span>
            <h3>{step.title}</h3>
            <p>{step.body}</p>
          </div>
          {i < steps.length - 1 && (
            <span className="method-flow-arrow" aria-hidden="true">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path
                  d="M5 12h13m0 0-5-5m5 5-5 5"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
