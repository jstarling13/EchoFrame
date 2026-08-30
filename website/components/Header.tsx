"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PRIMARY_NAV } from "@/lib/nav";
import MobileNav from "./MobileNav";

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="site-header">
      <div className="bar">
        <Link href="/" className="brand-mark">
          <Image
            src="/images/logo-mark-black.png"
            alt=""
            width={32}
            height={32}
            className="brand-mark-icon"
            priority
          />
          White Oak Operations
        </Link>
        <nav className="primary-nav" aria-label="Primary">
          <ul>
            {PRIMARY_NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={pathname === item.href ? "page" : undefined}
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/contact" className="btn btn-primary">
                Book a fit call
              </Link>
            </li>
          </ul>
        </nav>
        <MobileNav />
      </div>
    </header>
  );
}
