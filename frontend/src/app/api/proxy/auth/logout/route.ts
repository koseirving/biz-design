import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Get cookies from request to forward to backend
    const accessToken = request.cookies.get('access_token')?.value;
    const refreshToken = request.cookies.get('refresh_token')?.value;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    // Forward cookies to backend
    if (accessToken || refreshToken) {
      let cookieHeader = '';
      if (accessToken) cookieHeader += `access_token=${accessToken}; `;
      if (refreshToken) cookieHeader += `refresh_token=${refreshToken}; `;
      headers['Cookie'] = cookieHeader;
    }
    
    const response = await fetch(`${BACKEND_URL}/auth/logout`, {
      method: 'POST',
      headers,
    });

    const data = await response.json();
    const nextResponse = NextResponse.json(data, { status: 200 });
    
    // Clear cookies on frontend
    nextResponse.cookies.delete('access_token');
    nextResponse.cookies.delete('refresh_token');

    return nextResponse;
  } catch (error) {
    console.error('Logout proxy error:', error);
    const nextResponse = NextResponse.json(
      { message: 'Logout successful' },
      { status: 200 }
    );
    
    // Clear cookies even if backend fails
    nextResponse.cookies.delete('access_token');
    nextResponse.cookies.delete('refresh_token');
    
    return nextResponse;
  }
}