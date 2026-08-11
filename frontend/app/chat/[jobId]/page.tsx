'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { Nav } from '@/components/Nav';
import { Button, Card, FullPageSpinner, Input } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useRequireAuth } from '@/lib/hooks';
import { chatService, wsUrl } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';

export default function ChatPage() {
    const { loading } = useRequireAuth();
    const { user } = useAuth();
    const params = useParams();
    const searchParams = useSearchParams();
    const jobId = Number(params.jobId);
    const receiverId = Number(searchParams.get('with'));

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [text, setText] = useState('');
    const [fetching, setFetching] = useState(true);
    const bottomRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (loading || !user) return;
        chatService.history(jobId).then(setMessages).finally(() => setFetching(false));

        const token = localStorage.getItem('token');
        const ws = new WebSocket(wsUrl(`/chat/ws?token=${token}`));
        ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                if (payload.type === 'new_message' && payload.data.job_id === jobId) {
                    setMessages((prev) => [...prev, payload.data]);
                }
            } catch {
                // ignore malformed frames
            }
        };
        wsRef.current = ws;
        return () => ws.close();
    }, [loading, user, jobId]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    if (loading || fetching || !user) return <FullPageSpinner />;

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!text.trim() || !receiverId) return;
        const msg = await chatService.send({ job_id: jobId, receiver_id: receiverId, content: text });
        setMessages((prev) => [...prev, msg]);
        setText('');
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <Nav />
            <div className="max-w-2xl mx-auto w-full px-6 py-8 flex-1 flex flex-col">
                <h1 className="text-2xl font-black mb-4">Conversation — Offre #{jobId}</h1>
                <Card className="flex-1 flex flex-col p-0 overflow-hidden">
                    <div className="flex-1 overflow-y-auto p-6 space-y-3 max-h-[60vh] min-h-[40vh]">
                        {messages.length === 0 && (
                            <p className="text-center text-gray-400 text-sm">
                                Aucun message pour le moment. Dites bonjour 👋
                            </p>
                        )}
                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={`flex ${msg.sender_id === user.id ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-[75%] px-4 py-2 rounded-2xl text-sm ${
                                        msg.sender_id === user.id
                                            ? 'bg-[#DC143C] text-white'
                                            : 'bg-gray-100 text-gray-900'
                                    }`}
                                >
                                    {msg.content}
                                </div>
                            </div>
                        ))}
                        <div ref={bottomRef} />
                    </div>
                    <form onSubmit={handleSend} className="border-t border-gray-100 p-4 flex gap-3">
                        <Input
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="Écrire un message..."
                            className="flex-1"
                        />
                        <Button type="submit" disabled={!text.trim()}>
                            Envoyer
                        </Button>
                    </form>
                </Card>
            </div>
        </div>
    );
}
