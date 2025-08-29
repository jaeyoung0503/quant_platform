// src/app/api/portfolio/route.ts
export async function POST(request: Request) {
  try {
    const portfolio = await request.json();
    
    // 포트폴리오 ID 생성
    const portfolioId = Date.now().toString();
    
    console.log('포트폴리오 저장:', portfolio.name);
    
    return Response.json({
      success: true,
      id: portfolioId
    });
    
  } catch (error) {
    return Response.json({
      success: false,
      error: "포트폴리오 저장 실패"
    }, { status: 500 });
  }
}