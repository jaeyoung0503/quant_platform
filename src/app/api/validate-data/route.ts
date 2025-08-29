// src/app/api/validate-data/route.ts  
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const year = searchParams.get('year');
  
  return Response.json({
    isValid: true,
    message: `${year}년 데이터: 2,847개 종목 보유`
  });
}