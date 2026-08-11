import Link from 'next/link';
import { Button, Card } from '@/components/ui';

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-blue-50 to-green-50 overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-[#DC143C] rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-[#3B82F6] rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-6xl mx-auto px-6 text-center">
          <div className="inline-block tunisian-gradient p-4 rounded-3xl mb-8 animate-fade-in">
            <span className="text-white text-6xl font-black">5</span>
          </div>

          <h1 className="text-7xl font-black text-gray-900 mb-6 animate-fade-in">
            edma<span className="text-[#DC143C]">.tn</span>
          </h1>

          <p className="text-2xl text-gray-700 mb-12 max-w-2xl mx-auto animate-fade-in">
            La plateforme de référence pour les services domestiques en Tunisie
          </p>

          <div className="flex gap-4 justify-center animate-fade-in">
            <Link href="/register">
              <Button variant="primary" size="lg">
                Commencer Maintenant
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline" size="lg">
                Se Connecter
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-4xl font-black text-center mb-16">
            Pourquoi choisir <span className="text-[#DC143C]">5edma.tn</span> ?
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: '🔍',
                title: 'Trouvez des Pros',
                description: 'Access à des milliers de professionnels vérifiés',
              },
              {
                icon: '💬',
                title: 'Chat en Temps Réel',
                description: 'Communiquez instantanément avec les travailleurs',
              },
              {
                icon: '💰',
                title: 'Paiement Sécurisé',
                description: 'Système de portefeuille et paiement escrow',
              },
              {
                icon: '🤖',
                title: 'IA Intégrée',
                description: 'Génération automatique de descriptions',
              },
              {
                icon: '⭐',
                title: 'Avis Vérifiés',
                description: 'Système de notation transparent',
              },
              {
                icon: '🚀',
                title: 'Boosts',
                description: 'Mettez en avant vos annonces',
              },
            ].map((feature, i) => (
              <Card key={i} hoverable className="text-center">
                <div className="text-5xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-black mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <div className="inline-block tunisian-gradient p-2 rounded-xl mb-4">
            <span className="text-white text-2xl font-black">5</span>
          </div>
          <p className="text-gray-400 mb-4">
            © 2026 5edma.tn - Excellence Digitale au Service des Artisans Tunisiens
          </p>
        </div>
      </footer>
    </div>
  );
}
