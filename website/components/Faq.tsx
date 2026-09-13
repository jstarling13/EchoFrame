interface FaqItem {
  question: string;
  answer: string;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    question: "Is the first conversation free?",
    answer:
      "Yes. The initial discovery call is free — 20-30 minutes to confirm the workflow is real and automation is the right answer. If it's complex enough to need real mapping, that discovery work is billed at the standard hourly rate before any implementation begins.",
  },
  {
    question: "Do you only train teams?",
    answer:
      "No. Training only exists to transfer ownership of something real — a workflow that's already been mapped, built, or actively designed. Training without an underlying system is just a workshop, and that's not what gets sold here.",
  },
  {
    question: "Do you require ChatGPT or Claude?",
    answer:
      "No single AI vendor gets picked by default. Every workflow is evaluated on cost, reliability, data handling, and maintenance burden — the model or tool is chosen to fit that, never the other way around.",
  },
  {
    question: "Will AI replace staff?",
    answer:
      "EchoFrame isn't sold as a headcount-replacement service. The engagement is built around measurable operating outcomes and clear ownership — what a business does with the capacity it creates afterward is a business decision, not something baked into the workflow.",
  },
  {
    question: "Can you use sensitive data?",
    answer:
      "Only after the data is classified, the right controls and vendor terms are confirmed, and the scope is agreed in writing. Some sensitive workflows get declined outright rather than forced through inadequate controls.",
  },
  {
    question: "Who owns the work?",
    answer:
      "The client owns the delivered system, its documentation, and the ability to run and extend it. EchoFrame keeps its own reusable methods and background tools, the same way any consultant keeps their own playbook — the written agreement spells out exactly where that line sits.",
  },
  {
    question: "Can you guarantee savings?",
    answer:
      "No. Value gets estimated from the current workflow using conservative assumptions, then measured after implementation. Reclaimed time is capacity, not automatically cash — treating it as guaranteed savings would be dishonest.",
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
