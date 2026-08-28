interface FaqItem {
  question: string;
  answer: string;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    question: "Do you only train teams?",
    answer:
      "No. Training is tied to implemented or clearly designed workflows.",
  },
  {
    question: "Do you require ChatGPT or Claude?",
    answer: "No. We compare appropriate options.",
  },
  {
    question: "Will AI replace staff?",
    answer:
      "The engagement is designed around operating outcomes and accountable roles, not a headcount promise.",
  },
  {
    question: "Can you use sensitive data?",
    answer:
      "Only after classification, authorization, vendor/control review, and written scope; some uses are declined.",
  },
  {
    question: "Who owns the work?",
    answer:
      "The contract identifies bespoke client deliverables, background methods, third-party materials, accounts, and transfer.",
  },
  {
    question: "Can you guarantee savings?",
    answer:
      "No. We baseline, classify, and measure effects without calling capacity cash savings.",
  },
];

export default function Faq() {
  return (
    <div className="faq">
      {FAQ_ITEMS.map((item) => (
        <details key={item.question}>
          <summary>{item.question}</summary>
          <p>{item.answer}</p>
        </details>
      ))}
    </div>
  );
}
