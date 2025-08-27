// app/api/proxy/[...path]/route.ts

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest('GET', request, params.path)
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest('POST', request, params.path)
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest('PUT', request, params.path)
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest('PATCH', request, params.path)
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest('DELETE', request, params.path)
}

async function handleRequest(
  method: string,
  request: NextRequest,
  pathSegments: string[]
) {
  try {
    const path = pathSegments.join('/')
    const searchParams = request.nextUrl.searchParams.toString()
    const queryString = searchParams ? `?${searchParams}` : ''
    
    const backendUrl = `${BACKEND_URL}/api/${path}${queryString}`
    
    // 요청 헤더 복사 (필요한 것만)
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }
    
    // Authorization 헤더가 있으면 복사
    const authHeader = request.headers.get('authorization')
    if (authHeader) {
      headers.authorization = authHeader
    }
    
    // User-Agent 설정
    headers['User-Agent'] = 'QuanTrade-Frontend/1.0'
    
    const options: RequestInit = {
      method,
      headers,
    }
    
    // POST/PUT/PATCH 요청의 경우 body 추가
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      try {
        const body = await request.text()
        if (body) {
          options.body = body
        }
      } catch (error) {
        console.warn('Body parsing failed:', error)
      }
    }
    
    console.log(`Proxying ${method} ${backendUrl}`)
    
    const response = await fetch(backendUrl, options)
    
    // 응답 헤더 복사
    const responseHeaders = new Headers()
    
    // CORS 헤더 설정
    responseHeaders.set('Access-Control-Allow-Origin', '*')
    responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
    responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    // Content-Type 복사
    const contentType = response.headers.get('content-type')
    if (contentType) {
      responseHeaders.set('Content-Type', contentType)
    }
    
    // 응답 내용 처리
    let responseData
    
    if (contentType?.includes('application/json')) {
      try {
        const text = await response.text()
        responseData = text ? JSON.parse(text) : {}
      } catch (error) {
        console.error('JSON parsing failed:', error)
        responseData = { error: 'Invalid JSON response from backend' }
      }
    } else {
      responseData = await response.text()
    }
    
    // 에러 상태코드 처리
    if (!response.ok) {
      console.error(`Backend error: ${response.status} - ${JSON.stringify(responseData)}`)
      
      return NextResponse.json(
        responseData || { error: `Backend returned ${response.status}` },
        { 
          status: response.status,
          headers: responseHeaders
        }
      )
    }
    
    return NextResponse.json(responseData, {
      status: response.status,
      headers: responseHeaders
    })
    
  } catch (error) {
    console.error('Proxy error:', error)
    
    // 네트워크 에러 등의 경우
    return NextResponse.json(
      { 
        error: 'Backend connection failed',
        message: error instanceof Error ? error.message : 'Unknown error',
        backend_url: BACKEND_URL
      },
      { 
        status: 503,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        }
      }
    )
  }
}

// OPTIONS 요청 처리 (CORS preflight)
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  })
}