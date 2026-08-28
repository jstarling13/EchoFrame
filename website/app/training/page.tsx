import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Training",
  description:
    "A workflow is not implemented until people can use it, verify it, and recover when it fails. Owner, manager, employee, and advanced builder tracks.",
};

const TRACKS = [
  { title: "Owner", body: "Strategic oversight, risk posture, and investment decisions." },
  { title: "Manager", body: "Running the workflow day to day and coaching the team." },
  { title: "Employee", body: "Operating the workflow, verification, and exception handling." },
  { title: "Advanced builder", body: "Extending and maintaining implemented workflows." },
];

export default function TrainingPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/training", label: "Training" }]} />
        <h1>A workflow is not implemented until people can use it, verify it, and recover when it fails.</h1>
        <p>
          Owner, manager, employee, and advanced builder tracks combine live
          practice, data rules, verification, exceptions, and competency
          checks.
        </p>
        <div className="grid grid-2" style={{ marginTop: "1.5rem" }}>
          {TRACKS.map((track) => (
            <div className="card" key={track.title}>
              <h3>{track.title}</h3>
              <p>{track.body}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
