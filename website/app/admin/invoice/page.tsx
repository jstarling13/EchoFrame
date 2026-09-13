"use client";

import { useId, useState } from "react";
import { HOURLY_RATE_USD, FOOD_STIPEND_USD_PER_DAY, formatUsd } from "@/lib/services";

interface ExtraItem {
  id: string;
  description: string;
  amount: string;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function toNumber(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : 0;
}

export default function InvoiceGeneratorPage() {
  const formId = useId();

  const [clientName, setClientName] = useState("");
  const [clientEmail, setClientEmail] = useState("");
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [invoiceDate, setInvoiceDate] = useState(todayIso());
  const [description, setDescription] = useState("");
  const [hours, setHours] = useState("");
  const [travelFee, setTravelFee] = useState("");
  const [foodDays, setFoodDays] = useState("");
  const [notes, setNotes] = useState("");
  const [extraItems, setExtraItems] = useState<ExtraItem[]>([]);

  const hoursNum = toNumber(hours);
  const travelFeeNum = toNumber(travelFee);
  const foodDaysNum = toNumber(foodDays);
  const professionalSubtotal = hoursNum * HOURLY_RATE_USD;
  const foodSubtotal = foodDaysNum * FOOD_STIPEND_USD_PER_DAY;
  const extraTotal = extraItems.reduce((sum, item) => sum + toNumber(item.amount), 0);
  const total = professionalSubtotal + travelFeeNum + foodSubtotal + extraTotal;

  function addExtraItem() {
    setExtraItems((items) => [
      ...items,
      { id: `${Date.now()}-${items.length}`, description: "", amount: "" },
    ]);
  }

  function updateExtraItem(id: string, patch: Partial<ExtraItem>) {
    setExtraItems((items) => items.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  function removeExtraItem(id: string) {
    setExtraItems((items) => items.filter((item) => item.id !== id));
  }

  return (
    <main id="content">
      <div className="container section invoice-form">
        <p className="eyebrow">Internal Tool &mdash; Not Public</p>
        <h1>Invoice Generator</h1>
        <p className="hint">
          Fills in a printable invoice from the fields below. Nothing here
          is saved anywhere &mdash; use your browser&rsquo;s Print
          (&#8984;/Ctrl+P) and &ldquo;Save as PDF&rdquo; once it looks right.
        </p>

        <div className="grid grid-2" style={{ marginTop: "1.5rem" }}>
          <div className="form-field">
            <label htmlFor={`${formId}-client-name`}>Client name</label>
            <input
              id={`${formId}-client-name`}
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor={`${formId}-client-email`}>Client email (optional)</label>
            <input
              id={`${formId}-client-email`}
              type="email"
              value={clientEmail}
              onChange={(e) => setClientEmail(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor={`${formId}-invoice-number`}>Invoice number</label>
            <input
              id={`${formId}-invoice-number`}
              value={invoiceNumber}
              onChange={(e) => setInvoiceNumber(e.target.value)}
              placeholder="e.g. 2026-014"
            />
          </div>
          <div className="form-field">
            <label htmlFor={`${formId}-invoice-date`}>Invoice date</label>
            <input
              id={`${formId}-invoice-date`}
              type="date"
              value={invoiceDate}
              onChange={(e) => setInvoiceDate(e.target.value)}
            />
          </div>
        </div>

        <div className="form-field">
          <label htmlFor={`${formId}-description`}>Engagement / workflow description</label>
          <input
            id={`${formId}-description`}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Bookkeeping automation &mdash; QuickBooks reconciliation workflow"
          />
        </div>

        <div className="grid grid-3" style={{ marginTop: "1rem" }}>
          <div className="form-field">
            <label htmlFor={`${formId}-hours`}>
              Hours worked (&times; {formatUsd(HOURLY_RATE_USD)}/hr)
            </label>
            <input
              id={`${formId}-hours`}
              type="number"
              min="0"
              step="0.25"
              value={hours}
              onChange={(e) => setHours(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor={`${formId}-travel`}>Travel fee ($)</label>
            <input
              id={`${formId}-travel`}
              type="number"
              min="0"
              step="1"
              value={travelFee}
              onChange={(e) => setTravelFee(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor={`${formId}-food-days`}>
              Onsite food-stipend days (&times; {formatUsd(FOOD_STIPEND_USD_PER_DAY)}/day)
            </label>
            <input
              id={`${formId}-food-days`}
              type="number"
              min="0"
              step="1"
              value={foodDays}
              onChange={(e) => setFoodDays(e.target.value)}
            />
          </div>
        </div>

        <div style={{ marginTop: "1.5rem" }}>
          <p style={{ fontWeight: 700, marginBottom: "0.5rem" }}>
            Additional line items (optional)
          </p>
          {extraItems.map((item) => (
            <div
              key={item.id}
              style={{ display: "flex", gap: "0.75rem", alignItems: "flex-end", marginBottom: "0.75rem" }}
            >
              <div className="form-field" style={{ flex: 2, marginBottom: 0 }}>
                <label htmlFor={`${formId}-extra-desc-${item.id}`}>Description</label>
                <input
                  id={`${formId}-extra-desc-${item.id}`}
                  value={item.description}
                  onChange={(e) => updateExtraItem(item.id, { description: e.target.value })}
                />
              </div>
              <div className="form-field" style={{ flex: 1, marginBottom: 0 }}>
                <label htmlFor={`${formId}-extra-amount-${item.id}`}>Amount ($)</label>
                <input
                  id={`${formId}-extra-amount-${item.id}`}
                  type="number"
                  min="0"
                  step="1"
                  value={item.amount}
                  onChange={(e) => updateExtraItem(item.id, { amount: e.target.value })}
                />
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => removeExtraItem(item.id)}
                aria-label={`Remove line item ${item.description || item.id}`}
              >
                Remove
              </button>
            </div>
          ))}
          <button type="button" className="btn btn-secondary" onClick={addExtraItem}>
            + Add line item
          </button>
        </div>

        <div className="form-field" style={{ marginTop: "1.5rem" }}>
          <label htmlFor={`${formId}-notes`}>Notes (optional, shown on invoice)</label>
          <textarea
            id={`${formId}-notes`}
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        <button
          type="button"
          className="btn btn-primary"
          style={{ marginTop: "1.5rem" }}
          onClick={() => window.print()}
        >
          Print / Save as PDF
        </button>
      </div>

      <div className="invoice-preview">
        <div className="invoice-preview__header">
          <div>
            <h2 style={{ margin: 0 }}>EchoFrame</h2>
            <p className="hint" style={{ margin: 0 }}>Jacob Starling</p>
            <p className="hint" style={{ margin: 0 }}>jacob.starling@echoframe.net &middot; (706) 366-1096</p>
          </div>
          <div style={{ textAlign: "right" }}>
            <h3 style={{ margin: 0 }}>INVOICE</h3>
            {invoiceNumber && <p style={{ margin: 0 }}>#{invoiceNumber}</p>}
            {invoiceDate && <p style={{ margin: 0 }}>{invoiceDate}</p>}
          </div>
        </div>

        <div className="invoice-preview__bill-to">
          <p style={{ fontWeight: 700, marginBottom: "0.25rem" }}>Bill to</p>
          <p style={{ margin: 0 }}>{clientName || "—"}</p>
          {clientEmail && <p style={{ margin: 0 }}>{clientEmail}</p>}
        </div>

        {description && <p style={{ fontStyle: "italic" }}>{description}</p>}

        <table className="offers" style={{ width: "100%" }}>
          <thead>
            <tr>
              <th>Description</th>
              <th style={{ textAlign: "right" }}>Amount</th>
            </tr>
          </thead>
          <tbody>
            {hoursNum > 0 && (
              <tr>
                <td>
                  Professional time &mdash; {hoursNum} hr{hoursNum === 1 ? "" : "s"} &times;{" "}
                  {formatUsd(HOURLY_RATE_USD)}/hr
                </td>
                <td style={{ textAlign: "right" }}>{formatUsd(professionalSubtotal)}</td>
              </tr>
            )}
            {travelFeeNum > 0 && (
              <tr>
                <td>Travel fee</td>
                <td style={{ textAlign: "right" }}>{formatUsd(travelFeeNum)}</td>
              </tr>
            )}
            {foodDaysNum > 0 && (
              <tr>
                <td>
                  Onsite food stipend &mdash; {foodDaysNum} day{foodDaysNum === 1 ? "" : "s"} &times;{" "}
                  {formatUsd(FOOD_STIPEND_USD_PER_DAY)}/day
                </td>
                <td style={{ textAlign: "right" }}>{formatUsd(foodSubtotal)}</td>
              </tr>
            )}
            {extraItems
              .filter((item) => item.description || toNumber(item.amount) > 0)
              .map((item) => (
                <tr key={item.id}>
                  <td>{item.description || "—"}</td>
                  <td style={{ textAlign: "right" }}>{formatUsd(toNumber(item.amount))}</td>
                </tr>
              ))}
          </tbody>
          <tfoot>
            <tr>
              <td style={{ fontWeight: 700 }}>Total</td>
              <td style={{ textAlign: "right", fontWeight: 700 }}>{formatUsd(total)}</td>
            </tr>
          </tfoot>
        </table>

        {notes && (
          <p className="hint" style={{ marginTop: "1rem", whiteSpace: "pre-wrap" }}>
            {notes}
          </p>
        )}
      </div>
    </main>
  );
}
