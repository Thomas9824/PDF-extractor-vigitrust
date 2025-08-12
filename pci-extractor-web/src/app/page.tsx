import { PdfUploadForm } from "@/components/pdf-upload-form"
import { WaitlistWrapper } from "@/components/box"
import type { Metadata } from "next"

export const dynamic = "force-static"

export const generateMetadata = async (): Promise<Metadata> => {
  return {
    title: {
      template: "PCI DSS Extractor | %s",
      default: "PCI DSS Extractor - Extract requirements from PDF documents",
    },
    description:
      "Extract PCI DSS requirements from PDF documents automatically. Simple, fast and secure.",
    openGraph: {
      type: "website",
      title: "PCI DSS Extractor",
      description: "Extract PCI DSS requirements from PDF documents automatically"
    },
    twitter: {
      card: "summary_large_image",
      title: "PCI DSS Extractor",
      description: "Extract PCI DSS requirements from PDF documents automatically"
    },
  }
}

export default async function Home() {
  return (
    <WaitlistWrapper>
      {/* Heading */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-medium text-slate-12 whitespace-pre-wrap text-pretty">
          PCI DSS Extractor
        </h1>
        <div className="text-slate-10 [&>p]:tracking-tight text-pretty">
          <p>Extract PCI DSS requirements from your PDF documents automatically. Get structured JSON output ready for your systems.</p>
        </div>
      </div>

      {/* Upload Form */}
      <div className="px-1 flex flex-col w-full self-stretch">
        <PdfUploadForm />
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 gap-4 w-full text-center">
        <div className="space-y-2">
          <div className="text-sm font-medium text-slate-12">🔍 Smart extraction</div>
          <div className="text-xs text-slate-10">Automatic detection of requirements and tests</div>
        </div>
        <div className="space-y-2">
          <div className="text-sm font-medium text-slate-12">🔒 100% secure</div>
          <div className="text-xs text-slate-10">Your files are never stored on our servers</div>
        </div>
        <div className="space-y-2">
          <div className="text-sm font-medium text-slate-12">📊 Structured format</div>
          <div className="text-xs text-slate-10">JSON ready for integration with your systems</div>
        </div>
      </div>
    </WaitlistWrapper>
  )
}