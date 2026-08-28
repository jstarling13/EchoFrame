import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";
import LeadForm from "@/components/LeadForm";

export const metadata: Metadata = {
  title: "Contact",
  description: "Bring one workflow that keeps stealing time or attention. Request a fit call.",
};

export default function ContactPage() {
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
        <LeadForm />
      </div>
    </main>
  );
}
