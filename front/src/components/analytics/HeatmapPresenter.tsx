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
  const hexColors = fr.colors.getHex({ isDark });

  // Mapping scores to DSFR colors
  const getColor = (score: number) => {
    if (score >= 85) return hexColors.decisions.background.flat.success.default;
    if (score >= 70) return hexColors.decisions.background.flat.info.default;
    if (score >= 50) return hexColors.decisions.background.flat.warning.default;
    return hexColors.decisions.background.flat.error.default;
  };

  const getHealthAttr = (score: number) => {
    if (score >= 85) return "healthy";
    if (score >= 70) return "info";
    if (score >= 50) return "warning";
    return "crisis";
  };

  const getIcon = (score: number) => {
    if (score >= 85) return "✅";
    if (score >= 70) return "🔵";
    if (score >= 50) return "⚠️";
    return "🚨";
  };

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
    const { x, y, width, height, direction, score } = props;
    const maxChars = Math.max(6, Math.floor(width / 8));
    const lines = wrapText(direction ?? "", maxChars);
    const lineHeight = 16;
    const totalTextHeight = lines.length * lineHeight + 18; // +18 for score line
    const startY = y + height / 2 - totalTextHeight / 2 + lineHeight;

    return (
      <g
        onClick={() => onClusterClick?.(direction)}
        style={{ cursor: "pointer" }}
        data-health={getHealthAttr(score)}
      >
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill={getColor(score)}
          stroke={isDark ? "#1e1e1e" : "#ffffff"}
          strokeWidth={2}
        />
        {width > 50 && height > 30 && (
          <text
            x={x + width / 2}
            textAnchor="middle"
            fill="#ffffff"
            fontSize={12}
            fontWeight="bold"
          >
            {lines.map((line, i) => (
              <tspan
                key={i}
                x={x + width / 2}
                y={startY + i * lineHeight}
              >
                {i === 0 ? `${getIcon(score)} ${line}` : line}
              </tspan>
            ))}
            <tspan
              x={x + width / 2}
              y={startY + lines.length * lineHeight}
              fontSize={11}
              fontWeight="normal"
              opacity={0.85}
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
      className="fr-container fr-my-4w"
      style={{ height: "400px", width: "100%" }}
    >
      <ResponsiveContainer
        width="100%"
        height="100%"
      >
        <Treemap
          data={data}
          dataKey="count"
          aspectRatio={4 / 3}
          stroke="#fff"
          content={<CustomContent />}
        >
          <RechartsTooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload as HeatmapData;
                return (
                  <div
                    className="fr-card fr-p-2w"
                    style={{
                      backgroundColor: isDark ? "#1e1e1e" : "white",
                      border: `1px solid ${hexColors.decisions.border.default.grey.default}`,
                      boxShadow: "0 2px 6px 0 rgba(0,0,0,0.2)",
                    }}
                  >
                    <p className="fr-text--bold fr-mb-1w">{item.direction}</p>
                    <p className="fr-text--sm fr-mb-0">Score: {item.score}%</p>
                    <p className="fr-text--sm fr-mb-0">Crises: {item.crises}</p>
                  </div>
                );
              }
              return null;
            }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
};

export default HeatmapPresenter;
