import type { ReactNode } from 'react';
import '@universal-ui/engine/theme.css';

export const metadata = {
  title: 'Portable UI Engine — Next.js consumer',
  description: 'Proof that ui-* primitives consume cleanly from a Next.js App Router app.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" data-theme="warm-precision">
      <body>{children}</body>
    </html>
  );
}
