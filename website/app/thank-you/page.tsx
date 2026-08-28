import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Thank you",
  description: "Your request was received.",
  robots: { index: false, follow: false },
};

export default async function ThankYouPage({
  searchParams,
}: {
  searchParams: Promise<{ leadId?: string; checkout?: string }>;
}) {
  const params = await searchParams;

  return (
    <main id="content">
      <div className="container section">
        <h1>Thank you.</h1>
        {params.checkout === "success" ? (
          <p>
            Your payment was received. We will confirm project details by
            email within two business days. Payment alone does not replace
            a signed Statement of Work.
          </p>
        ) : (
          <p>Your request was received. We will respond within two business days.</p>
        )}
        {params.leadId && (
          <p className="hint">Reference ID: {params.leadId}</p>
        )}
      </div>
    </main>
  );
}
