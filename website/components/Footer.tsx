import Image from "next/image";
import Link from "next/link";
import { FOOTER_COMPANY, FOOTER_SERVICES, FOOTER_LEGAL } from "@/lib/nav";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <h2 className="footer-brand">
              <Image
                src="/images/logo-mark-white.png"
                alt=""
                width={36}
                height={36}
                className="brand-mark-icon"
              />
              White Oak Operations
            </h2>
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
            &copy; {new Date().getFullYear()} White Oak Operations. See{" "}
            <Link href="/about">About</Link> for company details still
            pending finalization. Not a certification of legal, medical,
            accounting, cybersecurity, or regulatory compliance.
          </p>
        </div>
      </div>
    </footer>
  );
}
