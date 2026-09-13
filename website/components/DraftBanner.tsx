import { isProductionDeployment } from "@/lib/environment";

/**
 * Internal build-status reminder for local/Preview only. Never shown on
 * the real Production deployment.
 */
export default function DraftBanner() {
  if (isProductionDeployment()) return null;

  return (
    <p className="draft-banner" role="status">
      Working build — preview/development environment only.
    </p>
  );
}
