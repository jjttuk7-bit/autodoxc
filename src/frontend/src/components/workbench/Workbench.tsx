import { Download, RotateCcw } from "lucide-react";
import ChatPanel from "../chat/ChatPanel";
import Canvas from "../canvas/Canvas";
import SidePanel from "../side-panel/SidePanel";
import { useSession } from "../../state/session-store";
import { Button } from "../ui/button";
import { exportDocxUrl } from "../../api/client";

export default function Workbench() {
  const { docType, uiState, sessionId, sections, reset } = useSession();
  const canExport = sessionId !== null && sections.size > 0;

  const handleExport = () => {
    if (!sessionId) return;
    // 새 탭에서 다운로드 트리거. 백엔드가 Content-Disposition: attachment로 응답.
    window.open(exportDocxUrl(sessionId), "_blank");
  };

  const handleNewSession = () => {
    if (
      confirm(
        "새 세션을 시작하시겠습니까? 현재 진행 중인 작업은 URL에서 제거됩니다.",
      )
    ) {
      try {
        const url = new URL(window.location.href);
        url.searchParams.delete("s");
        window.history.replaceState({}, "", url.toString());
      } catch {
        // ignored
      }
      reset();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <header className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-3">
          <span className="font-semibold">autodoxc</span>
          <span className="text-gray-400">·</span>
          <span className="text-gray-700">
            {docType ? docType.ko_name : "문서 미선택"}
          </span>
          <span className="text-xs text-gray-400 ml-2 uppercase">{uiState}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          {uiState !== "idle" && (
            <Button variant="outline" size="sm" onClick={handleNewSession}>
              <RotateCcw className="h-3 w-3" />
              새 세션
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            disabled={!canExport}
            onClick={handleExport}
            title={
              canExport
                ? ".docx로 다운로드"
                : "세션 생성 후 활성화됩니다"
            }
          >
            <Download className="h-3 w-3" />
            .docx 내보내기
          </Button>
        </div>
      </header>
      <div className="flex flex-1 min-h-0">
        <ChatPanel />
        <Canvas />
        <SidePanel />
      </div>
    </div>
  );
}
