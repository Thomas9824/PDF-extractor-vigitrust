import { WaitlistWrapper } from "@/components/box"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "À propos - Convertisseur PDF",
  description: "Découvrez notre outil de conversion PDF simple et sécurisé",
}

export default function About() {
  return (
    <WaitlistWrapper>
      <div className="flex flex-col gap-6">
        <div className="space-y-1">
          <h1 className="text-2xl sm:text-3xl font-medium text-slate-12">À propos</h1>
          <p className="text-slate-10">Notre mission est de simplifier la conversion de vos documents PDF</p>
        </div>

        <div className="space-y-4 text-sm text-slate-11">
          <div className="space-y-2">
            <h2 className="text-base font-medium text-slate-12">🚀 Rapide et efficace</h2>
            <p>
              Notre technologie de pointe permet de convertir vos PDF en images haute qualité en quelques secondes
              seulement.
            </p>
          </div>

          <div className="space-y-2">
            <h2 className="text-base font-medium text-slate-12">🔒 Sécurité garantie</h2>
            <p>
              Vos fichiers sont automatiquement supprimés de nos serveurs après conversion. Nous ne stockons aucune
              donnée personnelle.
            </p>
          </div>

          <div className="space-y-2">
            <h2 className="text-base font-medium text-slate-12">💡 Simple d'utilisation</h2>
            <p>Interface intuitive, glisser-déposer, et téléchargement direct. Aucune inscription requise.</p>
          </div>
        </div>
      </div>
    </WaitlistWrapper>
  )
}
