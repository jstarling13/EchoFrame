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
  { href: "/services#workflow-discovery", label: "Workflow Discovery" },
  { href: "/services#bookkeeping-automation", label: "Financial Workflow Automation" },
  { href: "/services#process-automation", label: "Process Automation" },
  { href: "/services#staff-training", label: "Staff Training" },
  { href: "/services#ongoing-consulting", label: "Ongoing AI Consulting" },
];

export const FOOTER_LEGAL: NavItem[] = [
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/security", label: "Security" },
];
