import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Training",
  description:
    "Practical training for owners, managers, and staff using AI and automated workflows in real business operations.",
};

const TRACKS = [
  {
    title: "Owner",
    body: "Strategic oversight, risk posture, and investment decisions.",
    covers: [
      "What the workflow does and doesn't do, in plain language",
      "Where the risk sits, and what's already been controlled for",
      "How to judge whether the next automation is worth building",
    ],
  },
  {
    title: "Manager",
    body: "Running the workflow day to day and coaching the team.",
    covers: [
      "Reading the exception queue and knowing what needs a decision",
      "Coaching staff through the workflow without EchoFrame in the room",
      "When to escalate versus when to let the routine path run",
    ],
  },
  {
    title: "Employee",
    body: "Operating the workflow, verification, and exception handling.",
    covers: [
      "The actual steps, start to finish, with real data",
      "How to verify the output before trusting it",
      "What to do the moment something looks wrong",
    ],
  },
  {
    title: "Advanced builder",
    body: "Extending and maintaining implemented workflows.",
    covers: [
      "How the system is put together, not just how to click it",
      "Extending the workflow to a new case without breaking the old one",
      "What to check before swapping in a newer AI model or tool",
    ],
  },
];

export default function TrainingPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/training", label: "Training" }]} />
        <p className="eyebrow">Demonstrate & Transfer</p>
        <h1>A workflow is not implemented until people can use it, verify it, and recover when it fails.</h1>
        <p>
          Training is not a slide deck at the end. Each track is built
          directly from the workflow that was actually implemented &mdash;
          live practice, real exceptions, and a competency check before
          EchoFrame steps back.
        </p>

        <div className="page-photo">
          <Image
            src="/images/training-workshop.png"
            alt=""
            fill
            sizes="(max-width: 768px) 100vw, 76rem"
          />
        </div>

        <div className="grid grid-2" style={{ marginTop: "1.5rem", gap: "1.5rem" }}>
          {TRACKS.map((track) => (
            <div className="card" key={track.title}>
              <h3>{track.title}</h3>
              <p>{track.body}</p>
              <ul>
                {track.covers.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <p style={{ marginTop: "2rem" }}>
          Training is scoped alongside the implementation it supports &mdash;
          see <Link href="/services#staff-training">Staff Training</Link> for
          how it fits into an engagement.
        </p>
      </div>
    </main>
  );
}
