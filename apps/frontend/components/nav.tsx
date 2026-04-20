import Link from "next/link";

export function Nav() {
  return (
    <nav className="border-b bg-white px-6 py-4 flex items-center gap-8">
      <span className="font-bold text-lg tracking-tight">Shelfy</span>
      <div className="flex gap-6 text-sm">
        <Link href="/ingest" className="text-gray-600 hover:text-gray-900">Ingest</Link>
        <Link href="/planogram" className="text-gray-600 hover:text-gray-900">Planogram</Link>
        <Link href="/arrange" className="text-gray-600 hover:text-gray-900">Arrange</Link>
        <Link href="/audit" className="text-gray-600 hover:text-gray-900">Audit</Link>
      </div>
      <span className="ml-auto text-xs text-gray-400 bg-yellow-100 px-2 py-1 rounded">
        POC — Synthetic Data
      </span>
    </nav>
  );
}
