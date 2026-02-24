import { cookies } from 'next/headers';
import { jwtVerify, type JWTPayload } from 'jose';
import { redirect } from 'next/navigation';

async function getCurrentUser(): Promise<JWTPayload> {
  const token = (await cookies()).get('token')?.value;
  if (!token) redirect('/login');

  const key = new TextEncoder().encode(process.env.JWT_SECRET!);
  const { payload } = await jwtVerify(token, key);
  return payload;
}

export default async function DashboardPage() {
  const user = await getCurrentUser();

  return (
    <main style={{ maxWidth: 600, margin: '60px auto', padding: '0 16px', fontFamily: 'system-ui' }}>
      <h1 style={{ fontSize: '1.5rem' }}>Dashboard</h1>

      <div style={{ border: '1px solid #eee', borderRadius: 8, padding: 20, marginBottom: 20 }}>
        <h2 style={{ marginTop: 0 }}>Signed in as</h2>
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <tbody>
            {[
              ['Name',     user['name']     as string],
              ['Email',    user['email']    as string],
              ['Provider', user['provider'] as string],
              ['User ID',  user.sub!],
            ].map(([label, value]) => (
              <tr key={label}>
                <td style={{ padding: '6px 12px 6px 0', fontWeight: 600, width: 100 }}>{label}</td>
                <td style={{ padding: '6px 0' }}>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <details style={{ marginBottom: 20 }}>
        <summary style={{ cursor: 'pointer', userSelect: 'none' }}>Full JWT payload</summary>
        <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 13, overflow: 'auto' }}>
          {JSON.stringify(user, null, 2)}
        </pre>
      </details>

      {/* Logout — uses a small client component so we can call the API */}
      <LogoutButton />
    </main>
  );
}

// Tiny client component just for the logout button
// (Server Components can't attach onClick handlers)
import LogoutButton from './LogoutButton';
