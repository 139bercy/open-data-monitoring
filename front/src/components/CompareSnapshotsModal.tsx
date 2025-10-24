import { createModal } from "@codegouvfr/react-dsfr/Modal";
import ReactDiffViewer from "react-diff-viewer-continued";
import type { SnapshotVersion } from "../types/datasets";

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

  return (
      <compareSnapshotsModal.Component title="Comparaison des versions" size="lg">
        <ReactDiffViewer
            oldValue={left}
            newValue={right}
            splitView={false}
            hideLineNumbers={false}
            leftTitle={new Date(snapshotB.timestamp).toLocaleString()}
            rightTitle={new Date(snapshotA.timestamp).toLocaleString()}
            useDarkTheme={false}
            styles={{
              wordDiff: {padding: 0},
              contentText: {wordBreak: 'break-word'}  // Force le wrapping du texte long
            }}
        />
      </compareSnapshotsModal.Component>
  );
}
