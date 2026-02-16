import { useState } from "react";
import { getToken } from "./api";
import Login from "./pages/Login";
import TransactionsPage from "./pages/TransactionsPage";

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());

  if (!authed) return <Login onOk={() => setAuthed(true)} />;

  return (
    <div style={{ padding: 20 }}>
      <TransactionsPage />
    </div>
  );
}
