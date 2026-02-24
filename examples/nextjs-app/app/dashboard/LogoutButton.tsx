'use client';

import { useRouter } from 'next/navigation';

export default function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'DELETE' });
    router.push('/login');
  }

  return (
    <button
      onClick={handleLogout}
      style={{
        padding: '9px 18px',
        background: '#fff',
        color: '#333',
        border: '1px solid #ccc',
        borderRadius: 4,
        cursor: 'pointer',
        fontSize: 14,
      }}
    >
      Sign out
    </button>
  );
}
