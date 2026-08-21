export default {
  async fetch(request, env) {
    const cors = {
      'Access-Control-Allow-Origin': 'https://bruhwiks.com',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Content-Type': 'application/json'
    };
    if (request.method === 'OPTIONS') return new Response(null, { headers: cors });
    if (request.method !== 'POST') return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405, headers: cors });

    try {
      const { message, history = [] } = await request.json();
      if (!message || typeof message !== 'string') return new Response(JSON.stringify({ error: 'Missing message' }), { status: 400, headers: cors });

      const recent = Array.isArray(history) ? history.slice(-8) : [];
      const input = [
        ...recent.map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: String(m.content || '').slice(0, 800) })),
        { role: 'user', content: message.slice(0, 1000) }
      ];

      const response = await fetch('https://api.openai.com/v1/responses', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'gpt-5.6',
          instructions: `You are Miamidian AI, the helpful support assistant for Sir. Miamidian's City. Keep replies concise, friendly, and useful. The Discord invite is https://discord.gg/WPEwDUtGfC. The community is strictly SFW. You can answer questions about the website, joining, roles, games, voice chats, rules, staff help, music, and general community questions. Never claim you performed staff actions. For reports, bans, appeals, or account-specific moderation issues, tell the user to contact real staff in Discord.`,
          input,
          max_output_tokens: 220
        })
      });

      if (!response.ok) {
        const detail = await response.text();
        return new Response(JSON.stringify({ error: 'AI request failed', detail }), { status: 502, headers: cors });
      }

      const data = await response.json();
      const text = data.output_text || data.output?.flatMap(x => x.content || []).find(x => x.type === 'output_text')?.text || 'Sorry, I could not generate a reply.';
      return new Response(JSON.stringify({ reply: text }), { headers: cors });
    } catch (err) {
      return new Response(JSON.stringify({ error: 'Server error' }), { status: 500, headers: cors });
    }
  }
};