import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
} from "recharts";
import type { SnapshotVersion } from "../../types/datasets";

interface TrafficChartProps {
  versions: SnapshotVersion[];
  datasetTitle?: string;
  datasetSlug?: string;
  platformName?: string;
  datasetUrl?: string;
}

const TrafficChart: React.FC<TrafficChartProps> = ({
  versions,
  datasetTitle,
  datasetSlug,
  platformName,
  datasetUrl,
}) => {
  const [aggregation, setAggregation] = React.useState<"daily" | "weekly">(
    "daily"
  );
  const [viewMode, setViewMode] = React.useState<"cumulative" | "delta">(
    "delta"
  );

  const chartData = useMemo(() => {
    // 1. Trier par date croissante
    const sortedRaw = [...versions].sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // DEDUPLICATION: Filtrer les snapshots "stagnants" (métriques identiques au précédent)
    // Cela crée des "trous" artificiels que l'interpolation viendra lisser.
    const sorted: SnapshotVersion[] = [];
    for (let i = 0; i < sortedRaw.length; i++) {
      const current = sortedRaw[i];
      const previous = i > 0 ? sortedRaw[i - 1] : null;

      if (previous && i < sortedRaw.length - 1) {
        const isStale =
          current.viewsCount === previous.viewsCount &&
          current.apiCallsCount === previous.apiCallsCount &&
          current.downloadsCount === previous.downloadsCount;
        if (isStale) continue;
      }
      sorted.push(current);
    }

    // 2. Filtrer pour les 90 derniers jours
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
    ninetyDaysAgo.setHours(0, 0, 0, 0);

    const filtered = sorted.filter(
      (v) => new Date(v.timestamp) >= ninetyDaysAgo
    );

    const formatDataPoint = (
      current: SnapshotVersion,
      previous?: SnapshotVersion
    ) => {
      const isDelta = viewMode === "delta";

      const diffMs = previous
        ? new Date(current.timestamp).getTime() -
          new Date(previous.timestamp).getTime()
        : 0;
      const diffDays = diffMs / (1000 * 60 * 60 * 24);
      const hasTemporalGap = diffDays > 3;

      const getValues = (
        curr: number | null | undefined,
        prev: number | null | undefined
      ) => {
        const absolute = curr ?? null;
        // Si c'est le tout premier point de l'histoire (pas de previous), on affiche 0 ou null?
        // On préfère null pour ne pas avoir de pic artificiel sur le premier point
        const delta =
          !previous || hasTemporalGap
            ? null
            : Math.max(0, (curr ?? 0) - (prev ?? 0));
        return { absolute, delta };
      };

      const viewsVals = getValues(current.viewsCount, previous?.viewsCount);
      const apiVals = getValues(current.apiCallsCount, previous?.apiCallsCount);
      const dlVals = getValues(
        current.downloadsCount,
        previous?.downloadsCount
      );

      return {
        date: new Date(current.timestamp).toLocaleDateString("fr-FR", {
          day: "numeric",
          month: "short",
        }),
        fullDate: new Date(current.timestamp).toLocaleDateString("fr-FR"),
        // Main data key for Recharts (depends on viewMode)
        views: isDelta ? viewsVals.delta : viewsVals.absolute,
        apiCalls: isDelta ? apiVals.delta : apiVals.absolute,
        downloads: isDelta ? dlVals.delta : dlVals.absolute,
        // Hidden keys for the tooltip
        _viewsAbs: viewsVals.absolute,
        _viewsDelta: viewsVals.delta,
        _apiAbs: apiVals.absolute,
        _apiDelta: apiVals.delta,
        _dlAbs: dlVals.absolute,
        _dlDelta: dlVals.delta,
      };
    };

    if (aggregation === "daily") {
      // 1. Regroupement par jour ISO
      const dailyMap = new Map<string, SnapshotVersion>();
      filtered.forEach((v) => {
        const dStr = new Date(v.timestamp).toISOString().split("T")[0];
        if (
          !dailyMap.has(dStr) ||
          new Date(v.timestamp) > new Date(dailyMap.get(dStr)!.timestamp)
        ) {
          dailyMap.set(dStr, v);
        }
      });

      // 2. Préparation des points calendaires
      const points: any[] = [];
      const cursor = new Date(ninetyDaysAgo);
      const today = new Date();
      today.setHours(23, 59, 59, 999);

      // snapshots ordonnés pour l'interpolation
      const timelineSnaps = Array.from(dailyMap.values()).sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );

      // Snapshot juste avant la fenêtre pour calcul du 1er delta
      const startRefIndex = sorted.findIndex(
        (v) => new Date(v.timestamp) >= ninetyDaysAgo
      );
      let globalLastKnown: SnapshotVersion | undefined =
        startRefIndex > 0 ? sorted[startRefIndex - 1] : undefined;

      while (cursor <= today) {
        const dStr = cursor.toISOString().split("T")[0];
        const nextSnapIndex = timelineSnaps.findIndex(
          (s) => new Date(s.timestamp).toISOString().split("T")[0] >= dStr
        );
        const nextSnap =
          nextSnapIndex !== -1 ? timelineSnaps[nextSnapIndex] : undefined;
        const prevSnap =
          nextSnapIndex > 0
            ? timelineSnaps[nextSnapIndex - 1]
            : globalLastKnown;

        let currentData: SnapshotVersion;

        if (dailyMap.has(dStr)) {
          currentData = dailyMap.get(dStr)!;
        } else if (prevSnap && nextSnap) {
          // INTERPOLATION GÉNÉRALE
          const tStart = new Date(prevSnap.timestamp).getTime();
          const tEnd = new Date(nextSnap.timestamp).getTime();
          const tCurrent = cursor.getTime();
          const ratio = (tCurrent - tStart) / (tEnd - tStart);

          const interpolate = (
            start: number | null | undefined,
            end: number | null | undefined
          ) => {
            if (start === undefined || start === null) return null;
            if (end === undefined || end === null) return null;
            return Math.round(start + (end - start) * ratio);
          };

          currentData = {
            ...nextSnap,
            timestamp: cursor.toISOString(),
            viewsCount: interpolate(prevSnap.viewsCount, nextSnap.viewsCount),
            apiCallsCount: interpolate(
              prevSnap.apiCallsCount,
              nextSnap.apiCallsCount
            ),
            downloadsCount: interpolate(
              prevSnap.downloadsCount,
              nextSnap.downloadsCount
            ),
          };
        } else {
          // LOCF (Si pas de "Next", on reste sur le dernier connu)
          currentData = prevSnap
            ? { ...prevSnap, timestamp: cursor.toISOString() }
            : ({} as SnapshotVersion);
        }

        if (currentData.timestamp) {
          const prevForDelta =
            points.length > 0
              ? points[points.length - 1]._raw
              : globalLastKnown;
          const formatted = formatDataPoint(currentData, prevForDelta);

          points.push({
            ...formatted,
            date: cursor.toLocaleDateString("fr-FR", {
              day: "numeric",
              month: "short",
            }),
            fullDate: cursor.toLocaleDateString("fr-FR"),
            _raw: currentData,
            _isInterpolated: !dailyMap.has(dStr),
          });
        }

        cursor.setDate(cursor.getDate() + 1);
      }

      return points;
    } else {
      // Agrégation par semaine
      const weeklyGroups: SnapshotVersion[] = [];
      filtered.forEach((v) => {
        const d = new Date(v.timestamp);
        const day = d.getDay() || 7;
        const monday = new Date(d);
        if (day !== 1) monday.setHours(-24 * (day - 1));
        const weekKey = monday.toISOString().split("T")[0];

        const existingIdx = weeklyGroups.findIndex((g) => {
          const gd = new Date(g.timestamp);
          const gday = gd.getDay() || 7;
          const gmonday = new Date(gd);
          if (gday !== 1) gmonday.setHours(-24 * (gday - 1));
          return gmonday.toISOString().split("T")[0] === weekKey;
        });

        if (existingIdx === -1) {
          weeklyGroups.push(v);
        } else if (
          new Date(v.timestamp) > new Date(weeklyGroups[existingIdx].timestamp)
        ) {
          weeklyGroups[existingIdx] = v;
        }
      });

      return weeklyGroups.map((v, idx) => {
        const prev =
          idx > 0
            ? weeklyGroups[idx - 1]
            : sorted[sorted.indexOf(filtered[0]) - 1];
        const point = formatDataPoint(v, prev);
        return {
          ...point,
          date: `Sem. ${new Date(v.timestamp).toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}`,
          fullDate: `Semaine du ${new Date(v.timestamp).toLocaleDateString("fr-FR")}`,
        };
      });
    }
  }, [versions, aggregation, viewMode]);

  // 3. Détecter les métriques actives
  const activeMetrics = useMemo(() => {
    const hasViews = chartData.some((d) => (d.views ?? 0) > 0);
    const hasApiCalls = chartData.some((d) => (d.apiCalls ?? 0) > 0);
    const hasDownloads = chartData.some((d) => (d.downloads ?? 0) > 0);

    return { views: hasViews, apiCalls: hasApiCalls, downloads: hasDownloads };
  }, [chartData]);

  if (chartData.length === 0) {
    return (
      <div className="fr-alert fr-alert--info fr-mt-2w">
        <p className="fr-text--sm">
          Aucune donnée de fréquentation disponible pour les 90 derniers jours.
        </p>
      </div>
    );
  }

  const renderControls = () => (
    <div className="fr-grid-row fr-grid-row--gutters fr-mb-2w">
      <div className="fr-col-12 fr-col-md-6">
        <label className="fr-label fr-text--xs fr-mb-1v">Agrégation</label>
        <div className="fr-btns-group fr-btns-group--sm fr-btns-group--inline">
          <button
            className={`fr-btn ${aggregation === "daily" ? "fr-btn--primary" : "fr-btn--secondary"}`}
            onClick={() => setAggregation("daily")}
          >
            Journalier
          </button>
          <button
            className={`fr-btn ${aggregation === "weekly" ? "fr-btn--primary" : "fr-btn--secondary"}`}
            onClick={() => setAggregation("weekly")}
          >
            Hebdomadaire
          </button>
        </div>
      </div>
      <div className="fr-col-12 fr-col-md-6">
        <label className="fr-label fr-text--xs fr-mb-1v">Mode de vue</label>
        <div className="fr-btns-group fr-btns-group--sm fr-btns-group--inline">
          <button
            className={`fr-btn ${viewMode === "delta" ? "fr-btn--primary" : "fr-btn--secondary"}`}
            onClick={() => setViewMode("delta")}
            title="Affiche l'accroissement (ex: +10 par jour)"
          >
            Flux (Deltas)
          </button>
          <button
            className={`fr-btn ${viewMode === "cumulative" ? "fr-btn--primary" : "fr-btn--secondary"}`}
            onClick={() => setViewMode("cumulative")}
            title="Affiche le total cumulé"
          >
            Cumulé
          </button>
        </div>
      </div>
    </div>
  );

  // Détermination dynamique des axes
  // Si pas de vues (ODS), on sépare API et DL sur deux axes pour voir les deltas
  const apiYAxisId = activeMetrics.views ? "right" : "left";
  const downloadsYAxisId = "right";

  return (
    <div
      style={{
        width: "100%",
        height: 600,
        marginTop: "1rem",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {renderControls()}
      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <LineChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 10, bottom: 20 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="var(--border-default-grey)"
            />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              stroke="var(--text-mention-grey)"
              minTickGap={20}
            />

            {/* Axe Gauche : Vues OU API (si pas de vues) */}
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11 }}
              stroke={activeMetrics.views ? "#000091" : "#e1000f"}
              width={50}
              domain={[0, "auto"]}
              hide={!activeMetrics.views && !activeMetrics.apiCalls}
              label={{
                value: activeMetrics.views
                  ? viewMode === "delta"
                    ? "Vues (+)"
                    : "Vues (tot.)"
                  : viewMode === "delta"
                    ? "API (+)"
                    : "API (tot.)",
                angle: -90,
                position: "insideLeft",
                offset: 10,
                fontSize: 10,
                fill: activeMetrics.views ? "#000091" : "#e1000f",
              }}
            />

            {/* Axe Droit : Volume (API/DL ou juste DL) */}
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11 }}
              stroke={
                activeMetrics.views ? "var(--text-mention-grey)" : "#00a95f"
              }
              width={50}
              domain={[0, "auto"]}
              hide={
                !activeMetrics.downloads &&
                (!activeMetrics.apiCalls || !activeMetrics.views)
              }
              label={{
                value: activeMetrics.views
                  ? viewMode === "delta"
                    ? "Usage (+)"
                    : "Usage (tot.)"
                  : viewMode === "delta"
                    ? "DL (+)"
                    : "DL (tot.)",
                angle: 90,
                position: "insideRight",
                offset: 10,
                fontSize: 10,
                fill: activeMetrics.views
                  ? "var(--text-mention-grey)"
                  : "#00a95f",
              }}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <div
                      className="fr-p-2w"
                      style={{
                        backgroundColor: "var(--background-raised-grey)",
                        border: "1px solid var(--border-default-grey)",
                        borderRadius: "4px",
                        boxShadow: "var(--shadow-raised-grey)",
                      }}
                    >
                      <p className="fr-text--sm fr-text--bold fr-mb-1w">
                        {label}
                      </p>
                      {payload.map((entry: any, index: number) => {
                        const data = entry.payload;
                        const name = entry.name;
                        const color = entry.color;

                        // Identify which hidden keys to use
                        let absVal = null;
                        let deltaVal = null;
                        if (name === "Vues") {
                          absVal = data._viewsAbs;
                          deltaVal = data._viewsDelta;
                        } else if (name === "Appels API") {
                          absVal = data._apiAbs;
                          deltaVal = data._apiDelta;
                        } else if (name === "Téléchargements") {
                          absVal = data._dlAbs;
                          deltaVal = data._dlDelta;
                        }

                        return (
                          <div
                            key={index}
                            className="fr-mb-1w"
                            style={{ color }}
                          >
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                gap: "1rem",
                                alignItems: "baseline",
                              }}
                            >
                              <span className="fr-text--xs fr-text--bold">
                                {name} :
                              </span>
                              <span className="fr-text--sm fr-text--bold">
                                {viewMode === "delta"
                                  ? deltaVal !== null
                                    ? `+${deltaVal.toLocaleString("fr-FR")}`
                                    : "N/A"
                                  : absVal !== null
                                    ? absVal.toLocaleString("fr-FR")
                                    : "N/A"}
                              </span>
                            </div>
                            <div
                              className="fr-text--xs"
                              style={{ opacity: 0.7, textAlign: "right" }}
                            >
                              {viewMode === "delta"
                                ? `Total: ${absVal?.toLocaleString("fr-FR") || "N/A"}`
                                : `Delta: ${deltaVal !== null ? `+${deltaVal.toLocaleString("fr-FR")}` : "N/A"}`}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend
              verticalAlign="top"
              height={36}
            />

            {activeMetrics.views && (
              <Line
                yAxisId="left"
                name="Vues"
                type="monotone"
                dataKey="views"
                stroke="#000091"
                strokeWidth={3}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
                connectNulls={true}
              />
            )}

            {activeMetrics.apiCalls && (
              <Line
                yAxisId={apiYAxisId}
                name="Appels API"
                type="monotone"
                dataKey="apiCalls"
                stroke="#e1000f"
                strokeWidth={2}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
                connectNulls={true}
              />
            )}

            {activeMetrics.downloads && (
              <Line
                yAxisId={downloadsYAxisId}
                name="Téléchargements"
                type="monotone"
                dataKey="downloads"
                stroke="#00a95f"
                strokeWidth={2}
                strokeDasharray={activeMetrics.views ? "5 5" : "0"}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
                connectNulls={true}
              />
            )}

            <Brush
              dataKey="date"
              height={30}
              stroke="var(--background-flat-blue-france)"
              fill="var(--background-alt-grey)"
              travellerWidth={10}
              gap={5}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div
        className="fr-mt-4w fr-p-4w"
        style={{
          backgroundColor: "var(--background-alt-grey)",
          borderRadius: "8px",
          border: "1px solid var(--border-default-grey)",
        }}
      >
        <div className="fr-grid-row fr-grid-row--middle">
          <div className="fr-col">
            <span
              className="fr-text--xs fr-mb-1v"
              style={{
                opacity: 0.6,
                textTransform: "uppercase",
                fontWeight: "bold",
              }}
            >
              Source des données
            </span>
            <p className="fr-text--sm fr-mb-0 fr-text--bold">
              {platformName || "Plateforme inconnue"} — {datasetSlug}
            </p>
            {datasetUrl && (
              <a
                href={datasetUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="fr-link fr-text--xs"
                style={{ wordBreak: "break-all" }}
              >
                {datasetUrl}
              </a>
            )}
          </div>
          <div className="fr-col--auto">
            <i
              className="ri-external-link-line"
              style={{ fontSize: "1.5rem", opacity: 0.2 }}
            ></i>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrafficChart;
