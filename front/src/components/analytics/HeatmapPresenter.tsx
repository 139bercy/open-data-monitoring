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
    if (score >= 80) return "#18753c"; // success-700
    if (score >= 30) return "#b34000"; // warning-625
    return "#e1000f"; // error-472
  };

  const getHealthAttr = (score: number) => {
    if (score >= 80) return "healthy";
    if (score >= 30) return "warning";
    return "crisis";
  };

  const CustomContent = (props: any) => {
    const { x, y, width, height, direction, score } = props;

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
          stroke="#fff"
          strokeWidth={2}
        />
        {width > 50 && height > 30 && (
          <text
            x={x + width / 2}
            y={y + height / 2}
            textAnchor="middle"
            fill="#fff"
            fontSize={14}
            fontWeight="bold"
          >
            {direction}
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
          dataKey="score"
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
