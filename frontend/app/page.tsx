'use client';

import Image from 'next/image';
import Link from 'next/link';
import { motion, type Variants } from 'framer-motion';
import { Button, Card } from '@/components/ui';

const fadeUp: Variants = {
    hidden: { opacity: 0, y: 24 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
};

const stagger: Variants = {
    hidden: {},
    show: { transition: { staggerChildren: 0.1 } },
};

const FEATURES = [
    {
        icon: '🔍',
        title: 'Trouvez le bon professionnel',
        description: 'Parcourez des travailleurs vérifiés par catégorie et localisation, ou publiez une offre et laissez les candidatures venir à vous.',
    },
    {
        icon: '🛡️',
        title: 'Profils vérifiés',
        description: "Chaque travailleur et client passe par une vérification d'identité avant de pouvoir publier ou postuler — pas d'anonymat.",
    },
    {
        icon: '💬',
        title: 'Chat en temps réel',
        description: "Discutez directement avec vos clients ou prestataires dans la plateforme, sans échanger de numéro avant d'être prêt.",
    },
    {
        icon: '💰',
        title: 'Portefeuille intégré',
        description: 'Rechargez votre solde, payez et recevez vos paiements en TND, avec un historique complet de vos transactions.',
    },
    {
        icon: '🤖',
        title: 'Assistant IA',
        description: 'Générez automatiquement votre bio professionnelle ou la description de votre offre grâce à notre assistant intelligent.',
    },
    {
        icon: '⭐',
        title: 'Avis transparents',
        description: 'Chaque mission terminée peut être notée — construisez votre réputation mission après mission.',
    },
];

const STEPS_CLIENT = [
    { step: '1', title: 'Publiez votre besoin', text: "Décrivez votre offre d'emploi ou recherchez un service déjà publié par un professionnel." },
    { step: '2', title: 'Choisissez un pro', text: 'Comparez les candidatures ou les profils, discutez, et sélectionnez le bon prestataire.' },
    { step: '3', title: 'Suivez et évaluez', text: 'Payez via votre portefeuille et laissez un avis une fois la mission terminée.' },
];

const STEPS_WORKER = [
    { step: '1', title: 'Créez votre profil', text: "Ajoutez vos compétences, votre tarif et votre localisation — ou générez votre bio avec l'IA." },
    { step: '2', title: 'Postulez ou publiez', text: 'Répondez aux offres qui vous correspondent, ou publiez vos propres services à prix fixe.' },
    { step: '3', title: 'Travaillez et encaissez', text: 'Discutez avec vos clients, réalisez la mission, et récupérez votre paiement dans votre portefeuille.' },
];

export default function HomePage() {
    return (
        <div className="min-h-screen overflow-x-hidden">
            {/* Hero */}
            <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-b from-white via-blue-50/40 to-white">
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute -top-32 -left-32 w-[32rem] h-[32rem] rounded-full bg-[var(--brand-red)]/10 blur-3xl animate-blob" />
                    <div className="absolute top-1/3 -right-40 w-[36rem] h-[36rem] rounded-full bg-[var(--brand-blue)]/10 blur-3xl animate-blob-delayed" />
                    <div className="absolute bottom-0 left-1/3 w-96 h-96 rounded-full bg-emerald-500/5 blur-3xl animate-blob" />
                </div>

                <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
                    <motion.div initial="hidden" animate="show" variants={stagger}>
                        <motion.div variants={fadeUp} className="inline-block mb-8">
                            <Image
                                src="/logo-icon.png"
                                alt="5edmaa.tn"
                                width={96}
                                height={84}
                                priority
                                className="h-20 w-auto mx-auto drop-shadow-[0_12px_24px_rgba(4,84,181,0.25)]"
                            />
                        </motion.div>

                        <motion.h1 variants={fadeUp} className="text-6xl sm:text-7xl font-black text-gray-900 mb-6 tracking-tight">
                            5<span className="text-gradient">edma</span>.tn
                        </motion.h1>

                        <motion.p variants={fadeUp} className="text-xl sm:text-2xl text-gray-600 mb-4 max-w-2xl mx-auto font-medium">
                            La plateforme de référence pour les services et l&apos;emploi local en Tunisie
                        </motion.p>
                        <motion.p variants={fadeUp} className="text-base text-gray-500 mb-12 max-w-xl mx-auto">
                            Trouvez un professionnel vérifié, ou proposez vos compétences — en toute confiance.
                        </motion.p>

                        <motion.div variants={fadeUp} className="flex flex-wrap gap-4 justify-center">
                            <Link href="/register">
                                <Button variant="primary" size="lg" className="shadow-luxury">
                                    Commencer maintenant
                                </Button>
                            </Link>
                            <Link href="/login">
                                <Button variant="outline" size="lg">
                                    Se connecter
                                </Button>
                            </Link>
                        </motion.div>
                    </motion.div>
                </div>

                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1, duration: 0.8 }}
                    className="absolute bottom-8 left-1/2 -translate-x-1/2 text-gray-400 text-sm flex flex-col items-center gap-2"
                >
                    <span>Découvrir</span>
                    <motion.span
                        animate={{ y: [0, 8, 0] }}
                        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
                    >
                        ↓
                    </motion.span>
                </motion.div>
            </section>

            {/* Features */}
            <section className="py-28 bg-white">
                <div className="max-w-6xl mx-auto px-6">
                    <motion.div
                        initial="hidden"
                        whileInView="show"
                        viewport={{ once: true, margin: '-80px' }}
                        variants={stagger}
                        className="text-center mb-16"
                    >
                        <motion.h2 variants={fadeUp} className="text-4xl sm:text-5xl font-black mb-4">
                            Pourquoi choisir <span className="text-gradient">5edma.tn</span> ?
                        </motion.h2>
                        <motion.p variants={fadeUp} className="text-gray-500 text-lg max-w-xl mx-auto">
                            Une plateforme pensée pour la confiance, des deux côtés.
                        </motion.p>
                    </motion.div>

                    <motion.div
                        initial="hidden"
                        whileInView="show"
                        viewport={{ once: true, margin: '-80px' }}
                        variants={stagger}
                        className="grid md:grid-cols-3 gap-6"
                    >
                        {FEATURES.map((feature) => (
                            <motion.div key={feature.title} variants={fadeUp}>
                                <Card hoverable className="h-full">
                                    <div className="w-14 h-14 rounded-2xl crimson-gradient flex items-center justify-center text-2xl mb-5 shadow-luxury">
                                        {feature.icon}
                                    </div>
                                    <h3 className="text-lg font-black mb-2">{feature.title}</h3>
                                    <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
                                </Card>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* How it works */}
            <section className="py-28 bg-gradient-to-b from-gray-50 to-white">
                <div className="max-w-6xl mx-auto px-6">
                    <motion.h2
                        initial="hidden"
                        whileInView="show"
                        viewport={{ once: true, margin: '-80px' }}
                        variants={fadeUp}
                        className="text-4xl sm:text-5xl font-black text-center mb-16"
                    >
                        Comment ça marche
                    </motion.h2>

                    <div className="grid md:grid-cols-2 gap-12">
                        <motion.div
                            initial="hidden"
                            whileInView="show"
                            viewport={{ once: true, margin: '-80px' }}
                            variants={stagger}
                        >
                            <motion.div variants={fadeUp} className="flex items-center gap-3 mb-8">
                                <span className="text-2xl">👤</span>
                                <h3 className="text-2xl font-black">Vous êtes client</h3>
                            </motion.div>
                            <div className="space-y-6">
                                {STEPS_CLIENT.map((s) => (
                                    <motion.div key={s.step} variants={fadeUp} className="flex gap-4">
                                        <div className="w-10 h-10 rounded-full blue-gradient text-white font-black flex items-center justify-center shrink-0">
                                            {s.step}
                                        </div>
                                        <div>
                                            <h4 className="font-bold mb-1">{s.title}</h4>
                                            <p className="text-gray-600 text-sm">{s.text}</p>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>

                        <motion.div
                            initial="hidden"
                            whileInView="show"
                            viewport={{ once: true, margin: '-80px' }}
                            variants={stagger}
                        >
                            <motion.div variants={fadeUp} className="flex items-center gap-3 mb-8">
                                <span className="text-2xl">🔧</span>
                                <h3 className="text-2xl font-black">Vous êtes travailleur</h3>
                            </motion.div>
                            <div className="space-y-6">
                                {STEPS_WORKER.map((s) => (
                                    <motion.div key={s.step} variants={fadeUp} className="flex gap-4">
                                        <div className="w-10 h-10 rounded-full crimson-gradient text-white font-black flex items-center justify-center shrink-0">
                                            {s.step}
                                        </div>
                                        <div>
                                            <h4 className="font-bold mb-1">{s.title}</h4>
                                            <p className="text-gray-600 text-sm">{s.text}</p>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Final CTA */}
            <section className="py-28 relative overflow-hidden">
                <div className="absolute inset-0 tunisian-gradient opacity-95" />
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-white/10 blur-3xl animate-blob" />
                </div>
                <motion.div
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, margin: '-80px' }}
                    variants={stagger}
                    className="relative z-10 max-w-3xl mx-auto px-6 text-center text-white"
                >
                    <motion.h2 variants={fadeUp} className="text-4xl sm:text-5xl font-black mb-6">
                        Prêt à commencer ?
                    </motion.h2>
                    <motion.p variants={fadeUp} className="text-lg text-white/90 mb-10">
                        Rejoignez 5edma.tn dès aujourd&apos;hui, que vous cherchiez un professionnel ou une mission.
                    </motion.p>
                    <motion.div variants={fadeUp}>
                        <Link href="/register">
                            <Button variant="white" size="lg">
                                Créer un compte gratuitement
                            </Button>
                        </Link>
                    </motion.div>
                </motion.div>
            </section>

            {/* Footer */}
            <footer className="bg-gray-900 text-white py-12">
                <div className="max-w-6xl mx-auto px-6 text-center">
                    <Image
                        src="/logo-icon.png"
                        alt="5edmaa.tn"
                        width={48}
                        height={42}
                        className="h-10 w-auto mx-auto mb-4 opacity-90"
                    />
                    <p className="text-gray-400 text-sm">
                        © {new Date().getFullYear()} 5edma.tn — Excellence digitale au service des artisans tunisiens
                    </p>
                </div>
            </footer>
        </div>
    );
}
