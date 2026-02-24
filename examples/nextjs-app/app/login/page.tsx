'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState('');
  const [providers, setProviders] = useState<string[]>([]);

  useEffect(() => {
    fetch('/api/providers')
      .then((r) => r.json())
      .then(({ providers }) => setProviders(providers));

    // Check for OAuth error in query param
    const params = new URLSearchParams(window.location.search);
    if (params.get('error') === 'auth_failed') setError('OAuth sign-in failed. Please try again.');
  }, []);

  async function handleLocalLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    const form = new FormData(e.currentTarget);

    const res = await fetch('/api/auth/local', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: form.get('username'),
        password: form.get('password'),
      }),
    });

    if (res.ok) {
      router.push('/dashboard');
    } else {
      const data = await res.json();
      setError(data.error ?? 'Login failed');
    }
  }

  return (
    <main style={{ maxWidth: 400, margin: '80px auto', padding: '0 16px', fontFamily: 'system-ui' }}>
      <h1 style={{ fontSize: '1.5rem' }}>Sign in to Authy Demo</h1>

      <form onSubmit={handleLocalLogin} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <label htmlFor="username">Username</label>
        <input
          id="username"
          name="username"
          placeholder="alice"
          autoComplete="username"
          required
          style={inputStyle}
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          placeholder="password123"
          autoComplete="current-password"
          required
          style={inputStyle}
        />

        {error && <p style={{ color: '#c00', fontSize: 14 }}>{error}</p>}

        <button type="submit" style={btnStyle}>Sign in</button>
      </form>

      {(providers.includes('google') || providers.includes('m365')) && (
        <>
          <hr style={{ margin: '20px 0' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {providers.includes('google') && (
              <a href="/api/auth/google" style={{ ...btnStyle, textAlign: 'center', textDecoration: 'none', background: '#fff', color: '#333', border: '1px solid #ccc' }}>
                Sign in with Google
              </a>
            )}
            {providers.includes('m365') && (
              <a href="/api/auth/m365" style={{ ...btnStyle, textAlign: 'center', textDecoration: 'none', background: '#fff', color: '#333', border: '1px solid #ccc' }}>
                Sign in with Microsoft 365
              </a>
            )}
          </div>
        </>
      )}

      <p style={{ marginTop: 20, fontSize: 13, color: '#666' }}>
        Test accounts: <code>alice / password123</code> or <code>bob / letmein</code>
      </p>
    </main>
  );
}

const inputStyle: React.CSSProperties = {
  padding: '8px 10px',
  border: '1px solid #ccc',
  borderRadius: 4,
  fontSize: 15,
};

const btnStyle: React.CSSProperties = {
  padding: '10px 16px',
  background: '#0070f3',
  color: '#fff',
  border: 'none',
  borderRadius: 4,
  fontSize: 15,
  cursor: 'pointer',
};
