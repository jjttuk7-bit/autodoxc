// B1-3: 자동 데모 SSE 연결 제거. 사용자가 StartScreen에서 입력 제출 → 세션 시작.
// session-store.startSession()이 POST → SSE 연결 흐름을 담당.

import Workbench from "./components/workbench/Workbench";

export default function App() {
  return <Workbench />;
}
