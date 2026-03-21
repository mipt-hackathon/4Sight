import Link from "next/link";

export default function HomePage() {
  return (
    <div className="page-card">
      <h1>Retail Analytics Scaffold</h1>
      <p className="muted">
        This frontend is intentionally minimal. Use the route shells below to build the MVP in
        parallel with backend, ML, and data work.
      </p>
      <ul>
        <li>
          <Link href="/dashboard">Dashboard overview</Link>
        </li>
        <li>
          <Link href="/customer/demo-user">Customer profile</Link>
        </li>
        <li>
          <Link href="/churn">Churn</Link>
        </li>
        <li>
          <Link href="/recommendations">Recommendations</Link>
        </li>
        <li>
          <Link href="/forecast">Forecast</Link>
        </li>
      </ul>
    </div>
  );
}
