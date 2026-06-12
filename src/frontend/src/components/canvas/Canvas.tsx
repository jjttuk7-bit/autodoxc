import { useSession } from "../../state/session-store";
import type { DraftParagraph, ParagraphStatus } from "../../api/types";
import StartScreen from "../start/StartScreen";

function statusClass(s: ParagraphStatus): string {
  switch (s) {
    case "confirmed":
      return "text-gray-900";
    case "inferred":
      return "text-gray-900 bg-yellow-100 border-b border-dotted border-yellow-500";
    case "defaulted":
      return "text-gray-500";
    case "evidence_backed":
      return "text-gray-900 border-r-2 border-blue-500 pr-2";
    case "empty":
      return "text-gray-400 italic bg-gray-50 border border-dashed border-gray-300 rounded px-1";
  }
}

function Paragraph({ p }: { p: DraftParagraph }) {
  return (
    <p className={`leading-relaxed py-1 ${statusClass(p.annotations.status)}`}>
      {p.text}
    </p>
  );
}

export default function Canvas() {
  const { uiState, skeleton, sections } = useSession();

  // 시작 전 — 입력 화면
  if (uiState === "idle") {
    return (
      <main className="flex-1 overflow-y-auto">
        <StartScreen />
      </main>
    );
  }

  const totalParas: DraftParagraph[] = Array.from(sections.values()).flatMap(
    (s) => s.paragraphs ?? []
  );
  const isConfirmed = (s: ParagraphStatus) =>
    s === "confirmed" || s === "evidence_backed";
  const isInferred = (s: ParagraphStatus) =>
    s === "inferred" || s === "defaulted";

  const confirmed = totalParas.filter((p) => isConfirmed(p.annotations.status)).length;
  const inferred = totalParas.filter((p) => isInferred(p.annotations.status)).length;
  const empty = totalParas.filter((p) => p.annotations.status === "empty").length;
  const total = totalParas.length || 1;
  const pct = (n: number) => Math.round((n / total) * 100);

  return (
    <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
      <div className="mb-4 max-w-3xl mx-auto">
        <div className="text-xs text-gray-500 mb-1 flex gap-4">
          <span>확정 {pct(confirmed)}%</span>
          <span>추정 {pct(inferred)}%</span>
          <span>빈칸 {pct(empty)}%</span>
        </div>
        <div className="h-1.5 bg-gray-200 rounded overflow-hidden flex">
          <div className="bg-gray-800" style={{ width: `${pct(confirmed)}%` }} />
          <div className="bg-yellow-400" style={{ width: `${pct(inferred)}%` }} />
          <div className="bg-gray-300" style={{ width: `${pct(empty)}%` }} />
        </div>
      </div>

      <article className="max-w-3xl mx-auto bg-white border border-gray-200 rounded shadow-sm p-8 space-y-6">
        {skeleton.length === 0 && (
          <div className="text-center text-gray-400 py-20">
            문서 골격 구성 중…
          </div>
        )}

        {skeleton.map((s) => {
          const filled = sections.get(s.id);
          const paras = filled?.paragraphs ?? [];
          return (
            <section key={s.id}>
              <h2 className="text-lg font-semibold mb-2 text-gray-900">
                {s.title}
              </h2>
              {paras.length > 0 ? (
                <div>
                  {paras.map((p, i) => (
                    <Paragraph key={i} p={p} />
                  ))}
                </div>
              ) : (
                <div className="text-gray-300 italic py-4">작성 중…</div>
              )}
            </section>
          );
        })}
      </article>
    </main>
  );
}
