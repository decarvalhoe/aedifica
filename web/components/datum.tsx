import React from "react";

const TS: Record<string, string> = {
  sourced: "is-sourced",
  computed: "is-computed",
  assumption: "is-assume",
  unknown: "is-unknown",
  conflict: "is-conflict",
  decision: "is-computed",
};

export function DsTs({ state }: { state: string }) {
  return (
    <span className={`ds-ts ${TS[state] || "is-unknown"}`}>
      <span className="dot" />
      {state}
    </span>
  );
}

export function Wordmark() {
  return (
    <span className="wordmark">
      <span className="ae">Æ</span>DIFICA
    </span>
  );
}
