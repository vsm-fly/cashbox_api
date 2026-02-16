import React, { useEffect, useState } from "react";
import type { Transaction, TransactionType } from "../transactions.api";
import {
  createTransaction,
  fetchTransactions,
  startTransactionsExportJob,
  getJobStatus,
  downloadJobResult,
} from "../transactions.api";

function toDatetimeLocalValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

function sleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

export default function TransactionsPage(): JSX.Element {
  const [items, setItems] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);

  const [type, setType] = useState<TransactionType>("expense");
  const [currency, setCurrency] = useState("RUB");
  const [amount, setAmount] = useState("");
  const [comment, setComment] = useState("");
  const [clientId, setClientId] = useState("");
  const [rate, setRate] = useState("");
  const [timestamp, setTimestamp] = useState(
    toDatetimeLocalValue(new Date())
  );

  const [creating, setCreating] = useState(false);
  const [exporting, setExporting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await fetchTransactions();
      setItems(data);
    } catch (e: any) {
      alert(e?.message ?? "Ошибка загрузки транзакций");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();

    const a = Number(amount.replace(",", "."));
    if (!Number.isFinite(a) || a <= 0)
      return alert("Сумма должна быть больше 0");

    const cid = clientId.trim() ? Number(clientId) : undefined;
    if (
      cid !== undefined &&
      (!Number.isFinite(cid) || cid <= 0)
    )
      return alert("ID клиента должен быть числом");

    const r = rate.trim()
      ? Number(rate.replace(",", "."))
      : undefined;
    if (r !== undefined && !Number.isFinite(r))
      return alert("Курс должен быть числом");

    setCreating(true);
    try {
      const created = await createTransaction({
        type,
        currency: currency.trim() || "RUB",
        amount: a,
        comment: comment.trim() || undefined,
        client_id: cid,
        rate: r,
        timestamp: timestamp
          ? new Date(timestamp).toISOString()
          : undefined,
      });

      setItems((prev) => [created, ...prev]);

      setAmount("");
      setComment("");
      setClientId("");
      setRate("");
      setTimestamp(toDatetimeLocalValue(new Date()));
    } catch (e: any) {
      alert(e?.message ?? "Ошибка создания транзакции");
    } finally {
      setCreating(false);
    }
  }

  async function onExport() {
    setExporting(true);
    try {
      const job = await startTransactionsExportJob({});
      const jobId = job.job_id;

      const maxAttempts = 60;
      for (let i = 0; i < maxAttempts; i++) {
        await sleep(2000);

        const st = await getJobStatus(jobId);

        if (st.status === "done") {
          const blob = await downloadJobResult(jobId);

          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `export_${new Date()
            .toISOString()
            .replace(/[:]/g, "-")
            .slice(0, 19)}.csv`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          window.URL.revokeObjectURL(url);

          return;
        }

        if (st.status === "failed") {
          throw new Error(
            st.error || "Ошибка экспорта"
          );
        }
      }

      throw new Error("Превышено время ожидания экспорта");
    } catch (e: any) {
      alert(e?.message ?? "Ошибка экспорта");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <h2 style={{ margin: 0 }}>Транзакции</h2>
          <div style={{ opacity: 0.7 }}>
            Всего: {items.length}
          </div>
        </div>
        <button
          onClick={onExport}
          disabled={exporting}
          style={{ padding: "8px 12px" }}
        >
          {exporting ? "Экспорт..." : "Экспорт"}
        </button>
      </header>

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 12,
          padding: 12,
        }}
      >
        <h3 style={{ marginTop: 0 }}>
          Создать транзакцию (приход / расход)
        </h3>

        <form
          onSubmit={onCreate}
          style={{
            display: "grid",
            gap: 10,
            gridTemplateColumns: "160px 160px 1fr 1fr",
          }}
        >
          <label>
            <span>Тип</span>
            <select
              value={type}
              onChange={(e) =>
                setType(
                  e.target.value as TransactionType
                )
              }
            >
              <option value="income">Приход</option>
              <option value="expense">Расход</option>
            </select>
          </label>

          <label>
            <span>Валюта</span>
            <input
              value={currency}
              onChange={(e) =>
                setCurrency(e.target.value)
              }
              placeholder="RUB"
            />
          </label>

          <label>
            <span>Сумма</span>
            <input
              value={amount}
              onChange={(e) =>
                setAmount(e.target.value)
              }
              placeholder="1000"
            />
          </label>

          <label>
            <span>Дата и время</span>
            <input
              type="datetime-local"
              value={timestamp}
              onChange={(e) =>
                setTimestamp(e.target.value)
              }
            />
          </label>

          <label>
            <span>ID клиента (необязательно)</span>
            <input
              value={clientId}
              onChange={(e) =>
                setClientId(e.target.value)
              }
              placeholder="1"
            />
          </label>

          <label>
            <span>Курс (необязательно)</span>
            <input
              value={rate}
              onChange={(e) =>
                setRate(e.target.value)
              }
              placeholder="1"
            />
          </label>

          <label style={{ gridColumn: "1 / -2" }}>
            <span>Комментарий</span>
            <input
              value={comment}
              onChange={(e) =>
                setComment(e.target.value)
              }
              placeholder="..."
            />
          </label>

          <button type="submit" disabled={creating}>
            {creating ? "Создание..." : "Создать"}
          </button>
        </form>
      </section>

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 12,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: 12,
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <h3 style={{ margin: 0 }}>Список</h3>
          <button
            onClick={() => void load()}
            disabled={loading}
          >
            {loading ? "Загрузка..." : "Обновить"}
          </button>
        </div>

        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
          }}
        >
          <thead>
            <tr>
              <th>Дата</th>
              <th>Тип</th>
              <th>Сумма</th>
              <th>Валюта</th>
              <th>Клиент</th>
              <th>Курс</th>
              <th>Комментарий</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id}>
                <td>
                  {new Date(
                    t.timestamp
                  ).toLocaleString()}
                </td>
                <td>{t.type === "income" ? "Приход" : "Расход"}</td>
                <td>
                  {t.type === "expense" ? "-" : "+"}
                  {t.amount}
                </td>
                <td>{t.currency}</td>
                <td>{t.client_id ?? ""}</td>
                <td>{t.rate ?? ""}</td>
                <td>{t.comment ?? ""}</td>
              </tr>
            ))}

            {items.length === 0 && !loading && (
              <tr>
                <td colSpan={7}>
                  Нет транзакций
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
