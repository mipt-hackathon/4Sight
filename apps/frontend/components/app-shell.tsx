import Link from "next/link";
import { ReactNode } from "react";


const navigation = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/customer/demo-user", label: "Customer Profile" },
  { href: "/churn", label: "Churn" },
  { href: "/recommendations", label: "Recommendations" },
  { href: "/forecast", label: "Forecast" },
];


export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <strong>Retail Analytics</strong>
        <p className="muted">Hackathon monorepo scaffold</p>
        <nav>
          {navigation.map((item) => (
            <Link key={item.href} href={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
