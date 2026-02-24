import { NextResponse } from 'next/server';
import { getAuthManager } from '@/lib/auth';

export async function GET() {
  const manager = await getAuthManager();
  return NextResponse.json({ providers: manager.listProviders() });
}
