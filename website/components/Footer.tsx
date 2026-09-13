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
                src="/images/echoframe-logo.png"
                alt="EchoFrame"
                width={118}
                height={31}
                className="brand-logo-full"
              />
            </h2>
            <p style={{ maxWidth: "32ch", opacity: 0.85 }}>
              Hands-on AI consulting for small businesses — workflow
              automation, financial systems, and training, billed hourly
              with no fixed packages.
            </p>
            <p style={{ maxWidth: "32ch", opacity: 0.85, marginTop: "1rem" }}>
              <a href="tel:+17063661096">(706) 366-1096</a>
              <br />
              <a href="mailto:jacob.starling@echoframe.net">
                jacob.starling@echoframe.net
              </a>
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
            &copy; {new Date().getFullYear()} EchoFrame, operated by Jacob
            Starling. Not a certification of legal, medical, accounting,
            cybersecurity, or regulatory compliance.
          </p>
        </div>
      </div>
    </footer>
  );
}
