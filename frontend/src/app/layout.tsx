import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

// Use Inter font
const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Company Research Assistant',
  description: 'Get information about companies, their financials, news, and stock performance',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="h-full bg-gray-50">{children}</body>
    </html>
  );
}