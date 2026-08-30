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
            src="/images/logo-full-white.png"
            alt="White Oak Operations"
            width={175}
            height={140}
            className="brand-logo-full"
            priority
          />
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
