// src/app/api/proxy/[...path]/route.ts
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

async function handleRequest(
  method: string,
  request: NextRequest,
  path: string[]
) {
  try {
    // path 배열을 문자열로 변환
    const pathString = path.join('/')
    const backendUrl = `${BACKEND_URL}/api/${pathString}`
    
    // URL에서 쿼리 파라미터 추출
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    const fullUrl = queryString ? `${backendUrl}?${queryString}` : backendUrl

    // 요청 옵션 설정
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    }

    // POST, PUT, PATCH 요청의 경우 body 추가
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      try {
        const body = await request.text()
        if (body) {
          options.body = body
        }
      } catch (error) {
        console.warn('Body 파싱 실패:', error)
      }
    }

    // 원본 요청의 헤더 복사 (필요한 것만)
    const originalHeaders = request.headers
    const allowedHeaders = ['authorization', 'user-agent', 'accept-language']
    
    allowedHeaders.forEach(header => {
      const value = originalHeaders.get(header)
      if (value && options.headers) {
        ;(options.headers as Record<string, string>)[header] = value
      }
    })

    console.log(`Proxying ${method} ${fullUrl}`)

    const response = await fetch(fullUrl, options)

    // 응답 헤더 복사
    const responseHeaders = new Headers()
    responseHeaders.set('Content-Type', response.headers.get('content-type') || 'application/json')
    responseHeaders.set('Access-Control-Allow-Origin', '*')
    responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    // 응답 본문 가져오기
    const responseText = await response.text()
    
    // JSON 응답인지 확인
    let responseData
    try {
      responseData = JSON.parse(responseText)
    } catch {
      responseData = responseText
    }

    console.log(`Backend response: ${response.status} ${response.statusText}`)

    if (!response.ok) {
      console.error(`Backend error: ${response.status} - ${responseText}`)
      return NextResponse.json(
        { 
          error: 'Backend service error',
          detail: responseData?.detail || `Backend returned ${response.status}`,
          status: response.status
        },
        { status: response.status, headers: responseHeaders }
      )
    }

    return NextResponse.json(responseData, {
      status: response.status,
      headers: responseHeaders
    })

  } catch (error: any) {
    console.error('Proxy error:', error)
    
    // 연결 오류인 경우
    if (error.code === 'ECONNREFUSED' || error.cause?.code === 'ECONNREFUSED') {
      return NextResponse.json(
        { 
          error: 'Backend service unavailable',
          detail: 'Backend server is not running. Please start the FastAPI server on port 8000.',
          suggestion: 'Run: cd backend && python main.py'
        },
        { status: 503 }
      )
    }

    return NextResponse.json(
      { 
        error: 'Proxy error',
        detail: error.message || 'Unknown proxy error'
      },
      { status: 500 }
    )
  }
}

// Next.js 15+ 호환 - params를 await로 처리
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return handleRequest('GET', request, resolvedParams.path)
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return handleRequest('POST', request, resolvedParams.path)
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return handleRequest('PUT', request, resolvedParams.path)
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return handleRequest('DELETE', request, resolvedParams.path)
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return handleRequest('PATCH', request, resolvedParams.path)
}

// OPTIONS 요청 처리 (CORS preflight)
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  })
}