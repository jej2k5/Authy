import { redirect } from 'next/navigation';

// Root route redirects to dashboard (middleware will redirect to /login if not authenticated)
export default function RootPage() {
  redirect('/dashboard');
}
