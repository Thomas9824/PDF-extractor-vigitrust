import { basehub } from "basehub"
import { PdfUploadForm } from "@/components/pdf-upload-form"
import { WaitlistWrapper } from "@/components/box"
import type { Metadata } from "next"
import "../basehub.config"

export const dynamic = "force-static"
export const revalidate = 30

export const generateMetadata = async (): Promise<Metadata> => {
  const data = await basehub().query({
    settings: {
      metadata: {
        titleTemplate: true,
        defaultTitle: true,
        defaultDescription: true,
        favicon: {
          url: true,
        },
        ogImage: {
          url: true,
        },
      },
    },
  })
  return {
    title: {
      template: "Convertisseur PDF | %s",
      default: "Convertisseur PDF - Transformez vos PDF facilement",
    },
    description:
      "Convertissez vos fichiers PDF en images haute qualité en quelques secondes. Simple, rapide et sécurisé.",
    openGraph: {
      type: "website",
      images: [data.settings.metadata.ogImage.url],
    },
    twitter: {
      card: "summary_large_image",
      images: [data.settings.metadata.ogImage.url],
    },
    icons: [data.settings.metadata.favicon.url],
  }
}

export default async function Home() {
  return (
    <WaitlistWrapper>
      {/* Heading */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-medium text-slate-12 whitespace-pre-wrap text-pretty">
          Convertisseur PDF
        </h1>
        <div className="text-slate-10 [&>p]:tracking-tight text-pretty">
          <p>Transformez vos fichiers PDF en images haute qualité en quelques secondes. Simple, rapide et sécurisé.</p>
        </div>
      </div>

      {/* Upload Form */}
      <div className="px-1 flex flex-col w-full self-stretch">
        <PdfUploadForm />
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 gap-4 w-full text-center">
        <div className="space-y-2">
          <div className="text-sm font-medium text-slate-12">✨ Conversion instantanée</div>
          <div className="text-xs text-slate-10">Vos PDF sont convertis en quelques secondes</div>
        </div>
        <div className="space-y-2">
          <div className="text-sm font-medium text-slate-12">🔒 100% sécurisé</div>
          <div className="text-xs text-slate-10">Vos fichiers sont supprimés automatiquement</div>
        </div>
        <div className="space-y-2">
          <div className="text-sm font-medium text-slate-12">📱 Tous formats</div>
          <div className="text-xs text-slate-10">PNG, JPG, WebP - Choisissez votre format</div>
        </div>
      </div>
    </WaitlistWrapper>
  )
}
