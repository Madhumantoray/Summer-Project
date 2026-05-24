import "./globals.css";

export const metadata = {
  title: "Stock Research Dashboard",
  description: "Quantitative market research dashboard for NSE equities",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
