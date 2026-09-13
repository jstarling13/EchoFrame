import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";
import LeadForm from "@/components/LeadForm";
import { INDUSTRY_OPTIONS, PROBLEM_OPTIONS, getOptionLabel } from "@/lib/industrySelector";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Talk with EchoFrame about a repetitive business workflow, automation opportunity, or AI implementation project.",
};

export default async function ContactPage({
  searchParams,
}: {
  searchParams: Promise<{ industry?: string; problem?: string }>;
}) {
  const params = await searchParams;
  const industryLabel = params.industry ? getOptionLabel(INDUSTRY_OPTIONS, params.industry) : undefined;
  const problemLabel = params.problem ? getOptionLabel(PROBLEM_OPTIONS, params.problem) : undefined;
  const prefill =
    industryLabel && problemLabel
      ? `Industry: ${industryLabel}\nWorkflow area: ${problemLabel}\n\n`
      : undefined;

  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/contact", label: "Contact" }]} />
        <h1>Bring one workflow that keeps stealing time or attention.</h1>
        <p>
          Tell us where work waits, repeats, or becomes inconsistent. Do not
          include confidential, privileged, health, financial-account,
          credential, or other sensitive information.
        </p>
        <LeadForm initialWorkflowProblem={prefill} />
      </div>
    </main>
  );
}
