import { Download, Save } from "lucide-react";
import ChatPanel from "../chat/ChatPanel";
import Canvas from "../canvas/Canvas";
import SidePanel from "../side-panel/SidePanel";
import { useSession } from "../../state/session-store";
import { Button } from "../ui/button";

export default function Workbench() {
  const { docType, uiState } = useSession();

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
          <Button variant="outline" size="sm">
            <Save className="h-3 w-3" />
            저장
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-3 w-3" />
            내보내기
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
