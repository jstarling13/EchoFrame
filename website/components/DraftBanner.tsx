import { isProductionDeployment } from "@/lib/environment";

/**
 * Internal build-status reminder for local/Preview only. Never shown on
 * the real Production deployment — real visitors should never see an
 * internal file reference or "working build" language.
 */
export default function DraftBanner() {
  if (isProductionDeployment()) return null;

  return (
    <p className="draft-banner" role="status">
      Working build — commercial constants are approved v1; legal pages are
      attorney-review drafts; company legal entity type, formation state,
      and registered agent are pending owner decisions. See
      IMPLEMENTATION_REPORT.md.
    </p>
  );
}
