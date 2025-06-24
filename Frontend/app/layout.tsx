import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Chat with Your Data',
  description: 'AI-powered data analysis tool',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}