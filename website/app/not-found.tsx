import Link from "next/link";

export default function NotFound() {
  return (
    <main id="content">
      <div className="container section">
        <h1>Page not found.</h1>
        <p>The page you are looking for does not exist or has moved.</p>
        <Link href="/" className="btn btn-primary">
          Return home
        </Link>
      </div>
    </main>
  );
}
