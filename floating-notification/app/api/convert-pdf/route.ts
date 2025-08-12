import { type NextRequest, NextResponse } from "next/server"
import { writeFile, mkdir, unlink } from "fs/promises"
import { join } from "path"
import { existsSync } from "fs"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("pdf") as File

    if (!file) {
      return NextResponse.json({ error: "Aucun fichier fourni" }, { status: 400 })
    }

    if (file.type !== "application/pdf") {
      return NextResponse.json({ error: "Le fichier doit être un PDF" }, { status: 400 })
    }

    // Create uploads directory if it doesn't exist
    const uploadsDir = join(process.cwd(), "public", "uploads")
    if (!existsSync(uploadsDir)) {
      await mkdir(uploadsDir, { recursive: true })
    }

    // Generate unique filename
    const timestamp = Date.now()
    const filename = `${timestamp}-${file.name.replace(/[^a-zA-Z0-9.-]/g, "_")}`
    const filepath = join(uploadsDir, filename)

    // Save the uploaded file
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filepath, buffer)

    // For demo purposes, we'll simulate PDF conversion
    // In a real app, you'd use libraries like pdf-poppler, pdf2pic, or similar
    const mockImages = [
      "/placeholder.svg?height=400&width=300&text=Page 1",
      "/placeholder.svg?height=400&width=300&text=Page 2",
      "/placeholder.svg?height=400&width=300&text=Page 3",
    ]

    // Clean up the uploaded PDF file
    setTimeout(async () => {
      try {
        await unlink(filepath)
      } catch (error) {
        console.error("Error cleaning up file:", error)
      }
    }, 60000) // Delete after 1 minute

    return NextResponse.json({
      filename: file.name,
      images: mockImages,
      downloadUrl: "/api/download-images?id=" + timestamp,
    })
  } catch (error) {
    console.error("Conversion error:", error)
    return NextResponse.json({ error: "Erreur lors de la conversion" }, { status: 500 })
  }
}
