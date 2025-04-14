'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
  const pathname = usePathname();
  
  return (
    <nav className="bg-blue-700 text-white">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex-shrink-0">
            <Link href="/" className="font-bold text-xl">
              Company Research
            </Link>
          </div>
          <div className="flex space-x-4">
            <Link
              href="/"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                pathname === '/' ? 'bg-blue-900' : 'hover:bg-blue-600'
              }`}
            >
              Chat
            </Link>
            <Link
              href="/stocks"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                pathname === '/stocks' ? 'bg-blue-900' : 'hover:bg-blue-600'
              }`}
            >
              Stocks
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}