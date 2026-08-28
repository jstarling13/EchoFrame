import Link from "next/link";

interface Crumb {
  href: string;
  label: string;
}

export default function Breadcrumbs({ trail }: { trail: Crumb[] }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol>
        <li>
          <Link href="/">Home</Link>
        </li>
        {trail.map((crumb, i) => (
          <li key={crumb.href} aria-current={i === trail.length - 1 ? "page" : undefined}>
            {i === trail.length - 1 ? crumb.label : <Link href={crumb.href}>{crumb.label}</Link>}
          </li>
        ))}
      </ol>
    </nav>
  );
}
