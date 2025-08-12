import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const id = searchParams.get("id")

  if (!id) {
    return NextResponse.json({ error: "ID manquant" }, { status: 400 })
  }

  // For demo purposes, return a simple response
  // In a real app, you'd create a ZIP file with all converted images
  return new NextResponse("Demo ZIP file content", {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="converted-images-${id}.zip"`,
    },
  })
}
