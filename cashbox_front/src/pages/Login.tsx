import { useState } from "react";
import { apiFetch, setToken } from "../api";

export default function Login({ onOk }: { onOk: () => void }) {
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const res = await apiFetch("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      setError("Login failed");
      return;
    }

    const data = await res.json();
    setToken(data.access_token);
    onOk();
  }

  return (
    <div style={{ maxWidth: 400, margin: "100px auto", fontFamily: "sans-serif" }}>
      <h2>Cashbox Login</h2>
      <form onSubmit={submit}>
        <input
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: "100%", marginBottom: 10 }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: "100%", marginBottom: 10 }}
        />
        <button style={{ width: "100%" }}>Login</button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
