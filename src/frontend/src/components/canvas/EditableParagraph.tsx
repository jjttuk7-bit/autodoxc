import { useEffect, useRef, useState } from "react";
import { Check, X } from "lucide-react";
import type { DraftParagraph, ParagraphStatus } from "../../api/types";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";

interface Props {
  paragraph: DraftParagraph;
  onSave: (newText: string) => void;
}

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

const EDITABLE_STATUSES: ReadonlySet<ParagraphStatus> = new Set<ParagraphStatus>(
  ["empty", "inferred", "defaulted"]
);

const PLACEHOLDER_REGEX = /\[\[([^\]]+)\]\]/g;

type Part =
  | { kind: "text"; value: string }
  | { kind: "ph"; label: string; rawMatch: string };

function splitByPlaceholders(text: string): Part[] {
  const parts: Part[] = [];
  let lastIndex = 0;
  PLACEHOLDER_REGEX.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = PLACEHOLDER_REGEX.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ kind: "text", value: text.slice(lastIndex, match.index) });
    }
    parts.push({ kind: "ph", label: match[1], rawMatch: match[0] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push({ kind: "text", value: text.slice(lastIndex) });
  }
  return parts;
}

interface SlotProps {
  label: string;
  rawMatch: string;
  fullText: string;
  onFill: (newText: string) => void;
}

function PlaceholderSlot({ label, rawMatch, fullText, onFill }: SlotProps) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const save = () => {
    const trimmed = value.trim();
    if (!trimmed) {
      setEditing(false);
      setValue("");
      return;
    }
    // 자리표시자 1개만 치환 — paragraph 전체 새 텍스트 생성
    const newText = fullText.replace(rawMatch, trimmed);
    onFill(newText);
    setEditing(false);
    setValue("");
  };

  if (editing) {
    const widthCh = Math.max(label.length + 2, value.length + 2);
    return (
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={save}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            save();
          }
          if (e.key === "Escape") {
            e.preventDefault();
            setValue("");
            setEditing(false);
          }
        }}
        placeholder={label}
        className="inline-block px-1.5 py-0.5 mx-0.5 border-2 border-blue-400 rounded text-sm bg-white align-baseline focus:outline-none not-italic"
        style={{ width: `${widthCh}ch`, minWidth: "6rem" }}
      />
    );
  }
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        setEditing(true);
      }}
      className="inline-block px-2 py-0.5 mx-0.5 bg-amber-50 hover:bg-amber-100 border border-dashed border-amber-400 rounded text-amber-800 text-[0.85em] align-baseline font-medium cursor-pointer transition-colors not-italic"
      title="클릭하여 채우기"
    >
      {label}
    </button>
  );
}

export default function EditableParagraph({ paragraph, onSave }: Props) {
  const [fullEditing, setFullEditing] = useState(false);
  const [fullValue, setFullValue] = useState(paragraph.text);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setFullValue(paragraph.text);
  }, [paragraph.text]);

  useEffect(() => {
    if (fullEditing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.select();
    }
  }, [fullEditing]);

  const status = paragraph.annotations.status;
  const parts = splitByPlaceholders(paragraph.text);
  const hasPlaceholders = parts.some((p) => p.kind === "ph");
  const isEditable = EDITABLE_STATUSES.has(status);

  // 전체 편집 모드 (자리표시자 없거나 더블클릭 진입)
  if (fullEditing) {
    return (
      <div className="my-1 border-2 border-blue-400 rounded p-1 bg-blue-50">
        <Textarea
          ref={textareaRef}
          value={fullValue}
          onChange={(e) => setFullValue(e.target.value)}
          className="border-0 bg-transparent focus-visible:ring-0 resize-none text-sm leading-relaxed"
          rows={2}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSave(fullValue);
              setFullEditing(false);
            }
            if (e.key === "Escape") {
              e.preventDefault();
              setFullValue(paragraph.text);
              setFullEditing(false);
            }
          }}
        />
        <div className="flex items-center justify-between mt-1 px-1">
          <div className="text-[10px] text-gray-500">
            <kbd className="px-1 py-0.5 bg-white rounded border">Enter</kbd> 저장 ·{" "}
            <kbd className="px-1 py-0.5 bg-white rounded border">Esc</kbd> 취소
          </div>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant="ghost"
              className="h-6 px-2"
              onClick={() => {
                setFullValue(paragraph.text);
                setFullEditing(false);
              }}
            >
              <X className="h-3 w-3" />
            </Button>
            <Button
              size="sm"
              className="h-6 px-2"
              onClick={() => {
                onSave(fullValue);
                setFullEditing(false);
              }}
            >
              <Check className="h-3 w-3" />
              저장
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // 자리표시자가 있는 paragraph: 인라인 input
  if (hasPlaceholders && isEditable) {
    return (
      <p
        className={`leading-relaxed py-1 ${statusClass(status)}`}
        onDoubleClick={() => {
          setFullValue(paragraph.text);
          setFullEditing(true);
        }}
        title="자리표시자 클릭 또는 더블클릭으로 전체 편집"
      >
        {parts.map((part, i) => {
          if (part.kind === "ph") {
            return (
              <PlaceholderSlot
                key={i}
                label={part.label}
                rawMatch={part.rawMatch}
                fullText={paragraph.text}
                onFill={onSave}
              />
            );
          }
          return <span key={i}>{part.value}</span>;
        })}
      </p>
    );
  }

  // 자리표시자 없는 paragraph: 전체 클릭 편집
  return (
    <p
      className={`leading-relaxed py-1 ${statusClass(status)} ${
        isEditable
          ? "cursor-pointer hover:ring-1 hover:ring-blue-300 hover:ring-offset-1 rounded transition-shadow"
          : ""
      }`}
      onClick={() => {
        if (isEditable) {
          setFullValue(paragraph.text);
          setFullEditing(true);
        }
      }}
      title={isEditable ? "클릭하여 편집" : undefined}
    >
      {paragraph.text}
    </p>
  );
}
