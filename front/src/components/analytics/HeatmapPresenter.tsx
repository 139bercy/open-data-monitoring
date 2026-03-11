import React from "react";
import { fr } from "@codegouvfr/react-dsfr";
import { useIsDark } from "@codegouvfr/react-dsfr/useIsDark";
import {
  ResponsiveContainer,
  Treemap,
  Tooltip as RechartsTooltip,
} from "recharts";

export interface HeatmapData {
  direction: string;
  score: number;
  crises: number;
  count: number;
  [key: string]: any; // Fix for Recharts Treemap typing
}

interface HeatmapPresenterProps {
  data: HeatmapData[];
  onClusterClick?: (direction: string) => void;
}

const HeatmapPresenter: React.FC<HeatmapPresenterProps> = ({
  data,
  onClusterClick,
}) => {
  const { isDark } = useIsDark();

  // Pre-process data for logarithmic sizing
  const processedData = React.useMemo(() => {
    return data.map((item) => ({
      ...item,
      logCount: Math.log10(item.count + 1) + 0.1, // Add small offset to ensure visibility
    }));
  }, [data]);

  // Continuous HSL color function for a "demanding" gradation
  // 0 -> Red (0°), 120 -> Green (120°)
  // We use a power function to make it "harder" to reach green
  const getColor = (score: number) => {
    const normalized = Math.min(100, Math.max(0, score)) / 100;
    // Power of 1.5 to stay longer in warm colors (orange/yellow)
    const hue = Math.pow(normalized, 1.5) * 125;
    const saturation = isDark ? 65 : 75;
    const lightness = isDark ? 35 : 45;
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  };

  const getHealthAttr = (score: number) => {
    if (score >= 90) return "excellent";
    if (score >= 75) return "healthy";
    if (score >= 50) return "warning";
    return "critical";
  };

  const getIcon = (score: number) => {
    if (score >= 95) return "🌟";
    if (score >= 85) return "✅";
    if (score >= 70) return "🍃";
    if (score >= 55) return "🟡";
    if (score >= 40) return "⚠️";
    if (score >= 25) return "🚨";
    return "🔥";
  };

  const [hoveredDir, setHoveredDir] = React.useState<string | null>(null);

  const wrapText = (text: string, maxCharsPerLine: number): string[] => {
    const words = text.split(" ");
    const lines: string[] = [];
    let current = "";
    for (const word of words) {
      if ((current + " " + word).trim().length <= maxCharsPerLine) {
        current = (current + " " + word).trim();
      } else {
        if (current) lines.push(current);
        current = word;
      }
    }
    if (current) lines.push(current);
    return lines;
  };

  const CustomContent = (props: any) => {
    const { x, y, width, height, direction, score, count } = props;
    const isHovered = hoveredDir === direction;
    const maxChars = Math.max(6, Math.floor(width / 8));
    const lines = wrapText(direction ?? "", maxChars);
    const lineHeight = 16;
    const totalTextHeight = lines.length * lineHeight + 36;
    const startY = y + height / 2 - totalTextHeight / 2 + lineHeight;

    return (
      <g
        onClick={() => onClusterClick?.(direction)}
        onMouseEnter={() => setHoveredDir(direction)}
        onMouseLeave={() => setHoveredDir(null)}
        style={{ cursor: "pointer", color: "#444444" }}
        fill="#444444"
        data-health={getHealthAttr(score)}
      >
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill={getColor(score)}
          stroke={
            isHovered
              ? isDark
                ? "#ffffff"
                : "#000000"
              : isDark
                ? "#1e1e1e"
                : "#ffffff"
          }
          strokeWidth={isHovered ? 3 : 1}
          style={{
            filter: isHovered ? "brightness(1.1) saturate(1.2)" : "none",
            transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        />
        {width > 40 && height > 25 && (
          <text
            x={x + width / 2}
            textAnchor="middle"
            fill="#444444"
            fontSize={isHovered ? 15 : 13}
            fontWeight="bold"
            style={{
              transition: "all 0.2s ease",
              pointerEvents: "none",
              fill: "#444444",
            }}
          >
            {lines.map((line, i) => (
              <tspan
                key={i}
                x={x + width / 2}
                y={startY + i * lineHeight}
                fill="#444444"
                style={{ fontWeight: "bold", fill: "#444444" }}
              >
                {i === 0 ? `${getIcon(score)} ${line}` : line}
              </tspan>
            ))}
            <tspan
              x={x + width / 2}
              y={startY + lines.length * lineHeight}
              fontSize={12}
              fontWeight="bold"
              fill="#444444"
              style={{ opacity: 0.9, fill: "#444444" }}
            >
              {Math.round(score)}%
            </tspan>
          </text>
        )}
      </g>
    );
  };

  return (
    <div
      id="heatmap-container"
      className="fr-container fr-my-4w"
      style={{ width: "100%" }}
    >
      <style>{`
        #heatmap-container text,
        #heatmap-container tspan {
          fill: #444444 !important;
          color: #444444 !important;
          stroke: none !important;
        }
      `}</style>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
        }}
      >
        <p
          className="fr-text--xs fr-mb-1w"
          style={{ color: "var(--text-mention-grey)", textAlign: "right" }}
        >
          📐 Échelle Logarithmique · 🎨 Couleur Continue
        </p>
      </div>

      <div style={{ height: "450px", width: "100%" }}>
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <Treemap
            data={processedData}
            dataKey="logCount"
            aspectRatio={4 / 3}
            stroke="#fff"
            content={<CustomContent />}
          >
            <RechartsTooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload as any;
                  return (
                    <div
                      className="fr-card fr-p-2w"
                      style={{ borderRadius: "2px" }}
                    >
                      <p className="fr-text--bold fr-mb-1w">{item.direction}</p>
                      <div className="fr-grid-row fr-grid-row--gutters fr-grid-row--sm">
                        <div className="fr-col-12">
                          <p className="fr-text--sm fr-mb-0">
                            Score Santé :{" "}
                            <span
                              style={{
                                color: getColor(item.score),
                                fontWeight: "bold",
                              }}
                            >
                              {item.score}%
                            </span>
                          </p>
                          <p className="fr-text--sm fr-mb-0">
                            Jeux de données :{" "}
                            <span className="fr-text--bold">{item.count}</span>
                          </p>
                          <p className="fr-text--sm fr-mb-0">
                            Crises détectées :{" "}
                            <span
                              className="fr-text--bold"
                              style={{ color: "var(--text-default-error)" }}
                            >
                              {item.crises}
                            </span>
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
          </Treemap>
        </ResponsiveContainer>
      </div>

      <div
        className="fr-mt-2w"
        style={{
          height: "8px",
          width: "100%",
          background: "linear-gradient(to right, #ff0000, #ffcc00, #00ff00)",
          borderRadius: "4px",
          display: "flex",
          justifyContent: "space-between",
          padding: "0 4px",
        }}
      >
        <span style={{ fontSize: "10px", marginTop: "12px", opacity: 0.6 }}>
          CRITIQUE
        </span>
        <span style={{ fontSize: "10px", marginTop: "12px", opacity: 0.6 }}>
          MOYEN
        </span>
        <span style={{ fontSize: "10px", marginTop: "12px", opacity: 0.6 }}>
          EXCELLENT
        </span>
      </div>
    </div>
  );
};

export default HeatmapPresenter;
