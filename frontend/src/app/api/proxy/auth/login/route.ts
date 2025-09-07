import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${BACKEND_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    // Create Next.js response with cookies from backend
    const nextResponse = NextResponse.json(data, { status: 200 });
    
    // Forward cookies from backend response
    const cookieHeader = response.headers.get('set-cookie');
    if (cookieHeader) {
      // Parse and set each cookie
      const cookies = cookieHeader.split(', ');
      cookies.forEach(cookie => {
        const [nameValue, ...options] = cookie.split('; ');
        const [name, value] = nameValue.split('=');
        
        // Parse cookie options
        let maxAge: number | undefined;
        let httpOnly = false;
        let secure = false;
        let sameSite: 'lax' | 'strict' | 'none' = 'lax';
        
        options.forEach(option => {
          const [key, val] = option.split('=');
          switch (key.toLowerCase()) {
            case 'max-age':
              maxAge = parseInt(val);
              break;
            case 'httponly':
              httpOnly = true;
              break;
            case 'secure':
              secure = true;
              break;
            case 'samesite':
              sameSite = val.toLowerCase() as 'lax' | 'strict' | 'none';
              break;
          }
        });
        
        nextResponse.cookies.set(name, value, {
          maxAge,
          httpOnly,
          secure,
          sameSite,
        });
      });
    }

    return nextResponse;
  } catch (error) {
    console.error('Login proxy error:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}