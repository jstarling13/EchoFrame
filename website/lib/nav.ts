export interface NavItem {
  href: string;
  label: string;
}

export const PRIMARY_NAV: NavItem[] = [
  { href: "/services", label: "Services" },
  { href: "/method", label: "Method" },
  { href: "/industries", label: "Industries" },
  { href: "/training", label: "Training" },
  { href: "/security", label: "Security" },
  { href: "/about", label: "About" },
];

export const FOOTER_COMPANY: NavItem[] = [
  { href: "/about", label: "About" },
  { href: "/method", label: "Method" },
  { href: "/insights", label: "Insights" },
  { href: "/contact", label: "Contact" },
];

export const FOOTER_SERVICES: NavItem[] = [
  { href: "/workflow-diagnostic", label: "Workflow Opportunity Diagnostic" },
  { href: "/build-sprint", label: "Workflow Build Sprint" },
  { href: "/transformation", label: "AI Operations Transformation" },
  { href: "/enterprise", label: "Enterprise AI Operations Program" },
  { href: "/support", label: "Workflow Assurance & Enablement" },
];

export const FOOTER_LEGAL: NavItem[] = [
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/security", label: "Security" },
];
