import Link from "next/link";
import { FOOTER_COMPANY, FOOTER_SERVICES, FOOTER_LEGAL } from "@/lib/nav";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <h2>Practical AI Operations</h2>
            <p style={{ maxWidth: "32ch", opacity: 0.85 }}>
              Vendor-neutral AI workflow consulting, implementation, and
              training for established businesses.
            </p>
          </div>
          <div>
            <h3>Company</h3>
            <ul>
              {FOOTER_COMPANY.map((item) => (
                <li key={item.href}>
                  <Link href={item.href}>{item.label}</Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Services</h3>
            <ul>
              {FOOTER_SERVICES.map((item) => (
                <li key={item.href}>
                  <Link href={item.href}>{item.label}</Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Legal</h3>
            <ul>
              {FOOTER_LEGAL.map((item) => (
                <li key={item.href}>
                  <Link href={item.href}>{item.label}</Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="footer-legal">
          <p>
            &copy; {new Date().getFullYear()} Practical AI Operations. Working
            brand name, pending trademark and domain screening — see{" "}
            <Link href="/about">About</Link>. Not a certification of legal,
            medical, accounting, cybersecurity, or regulatory compliance.
          </p>
        </div>
      </div>
    </footer>
  );
}
