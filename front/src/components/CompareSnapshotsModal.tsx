import { createModal } from "@codegouvfr/react-dsfr/Modal";
import ReactDiffViewer from "react-diff-viewer-continued";
import type { SnapshotVersion } from "../types/datasets";
import { useIsDark } from "@codegouvfr/react-dsfr/useIsDark";
import {useState} from "react";


export const compareSnapshotsModal = createModal({
  id: "compare-snapshots-modal",
  isOpenedByDefault: false,
});

type CompareSnapshotsModalProps = Readonly<{
  snapshotA: SnapshotVersion;
  snapshotB: SnapshotVersion;
}>;

export function CompareSnapshotsModal({
                                        snapshotA,
                                        snapshotB,
                                      }: CompareSnapshotsModalProps): JSX.Element {
  const left = JSON.stringify(snapshotB.data ?? {}, null, 2);
  const right = JSON.stringify(snapshotA.data ?? {}, null, 2);
  const [darkMode, setDarkMode] = useState(
      document.documentElement.getAttribute("data-fr-theme") === "dark"
  );

  return (
      <compareSnapshotsModal.Component title="Comparaison des versions" size="lg">
        <ReactDiffViewer
            oldValue={left}
            newValue={right}
            splitView={false}
            hideLineNumbers={false}
            leftTitle={new Date(snapshotB.timestamp).toLocaleString()}
            rightTitle={new Date(snapshotA.timestamp).toLocaleString()}
            useDarkTheme={darkMode}
            styles={{
              wordDiff: {padding: 0},
              contentText: {wordBreak: 'break-word'}
            }}
        />
      </compareSnapshotsModal.Component>
  );
}
