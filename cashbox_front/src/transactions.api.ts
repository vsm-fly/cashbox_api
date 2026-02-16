// src/transactions.api.ts
import { apiFetch, apiFetchJson } from "./api";

export type TransactionType = "income" | "expense";

export type Transaction = {
  id: number;
  type: TransactionType;
  currency: string;
  amount: number;
  comment?: string | null;
  client_id?: number | null;
  rate?: number | null;
  timestamp: string; // ISO
};

export type CreateTransactionRequest = {
  type: TransactionType;
  currency: string;
  amount: number;
  comment?: string;
  client_id?: number;
  rate?: number;
  timestamp?: string; // ISO
};

export async function fetchTransactions(): Promise<Transaction[]> {
  return apiFetchJson<Transaction[]>("/api/v1/transactions");
}

export async function createTransaction(payload: CreateTransactionRequest): Promise<Transaction> {
  return apiFetchJson<Transaction>("/api/v1/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/* =========================
   Export (jobs)
   ========================= */

export type ExportTransactionsRequest = {
  date_from?: string; // ISO
  date_to?: string; // ISO
  currency?: string;
  client_id?: number;
  type?: TransactionType;
};

export type ExportJobResponse = {
  job_id: string;
  status: "queued" | "running" | "done" | "failed" | string;
};

export type JobStatusResponse = {
  job_id: string;
  status: "queued" | "running" | "done" | "failed" | string;
  // если бэк добавит поля — будет не мешать
  detail?: unknown;
  error?: string | null;
};

// 1) Создать job на экспорт транзакций
export async function startTransactionsExportJob(
  payload: ExportTransactionsRequest = {},
): Promise<ExportJobResponse> {
  return apiFetchJson<ExportJobResponse>("/api/v1/jobs/exports/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// 2) Проверить статус job
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return apiFetchJson<JobStatusResponse>(`/api/v1/jobs/${jobId}`);
}

// 3) Скачать результат job (когда status === "done")
export async function downloadJobResult(jobId: string): Promise<Blob> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}/download`, { method: "GET" });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }

  return await res.blob();
}
