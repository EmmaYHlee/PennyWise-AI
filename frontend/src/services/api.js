const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function parseResponse(response) {
  if (response.ok) return response.json();
  const body = await response.json().catch(() => ({}));
  throw new Error(body.detail || `Backend request failed (${response.status})`);
}

export async function sendChatMessage(message, history = []) {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      history,
    }),
  });
  return parseResponse(response);
}

export async function getDashboard() {
  const response = await fetch(`${API_URL}/dashboard`);
  return parseResponse(response);
}
