import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EchoFrame Intelligence',
  description: 'Financial intelligence for small businesses',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
