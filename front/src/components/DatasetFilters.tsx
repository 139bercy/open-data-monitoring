import { useMemo } from "react";
import { Select } from "@codegouvfr/react-dsfr/Select";
import { Input } from "@codegouvfr/react-dsfr/Input";
import { Button } from "@codegouvfr/react-dsfr/Button";
import type {
  DatasetListQuery,
  PlatformRef,
  PublishersRef,
} from "../types/datasets";

export type DatasetFiltersProps = Readonly<{
  query: DatasetListQuery;
  platforms: PlatformRef[];
  publishers: PublishersRef;
  onChange: (partial: Partial<DatasetListQuery>) => void;
  onReset?: () => void;
}>;

export function DatasetFilters(props: DatasetFiltersProps): JSX.Element {
  const { query, platforms, publishers, onChange, onReset } = props;

  const platformOptions = useMemo(
    () => [
      { value: "", label: "Toutes les plateformes" },
      ...platforms.map((p) => ({ value: p.id, label: p.name ?? p.slug })),
    ],
    [platforms]
  );

  const publisherOptions = useMemo(
    () => [
      { value: "", label: "Tous les producteurs" },
      ...publishers.map((p) => ({ value: p, label: p })),
    ],
    [publishers]
  );

  return (
    <div
      className="fr-my-2w"
      style={{ width: "100%" }}
    >
      <div
        className="fr-grid-row fr-grid-row--gutters fr-grid-row--top"
        style={{ display: "flex", alignItems: "center" }}
      >
        <div className="fr-col-12 fr-col-md-4">
          <Input
            label="Rechercher par slug"
            // hintText="Recherche contenant (ILIKE) sur le slug"
            nativeInputProps={{
              type: "search",
              value: query.q ?? "",
              onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                onChange({ q: e.currentTarget.value, page: 1 }),
              placeholder: "ex: prix-des-controles-techniques",
            }}
            style={{ transition: "box-shadow .2s ease" }}
          />
        </div>
        <div className="fr-col-12 fr-col-md-4">
          <Select
            label="Plateforme"
            nativeSelectProps={{
              value: query.platformId ?? "",
              onChange: (e: React.ChangeEvent<HTMLSelectElement>) =>
                onChange({
                  platformId: e.currentTarget.value || undefined,
                  page: 1,
                }),
              style: { width: "100%", transition: "box-shadow .2s ease" },
            }}
          >
            {platformOptions.map((opt) => (
              <option
                key={opt.value}
                value={opt.value}
              >
                {opt.label}
              </option>
            ))}
          </Select>
        </div>
        <div className="fr-col-12 fr-col-md-4">
          <Select
            label="Producteur"
            nativeSelectProps={{
              value: query.publisher ?? "",
              onChange: (e: React.ChangeEvent<HTMLSelectElement>) =>
                onChange({
                  publisher: e.currentTarget.value || undefined,
                  page: 1,
                }),
              style: { width: "100%", transition: "box-shadow .2s ease" },
            }}
          >
            {publisherOptions.map((opt) => (
              <option
                key={opt.value}
                value={opt.value}
              >
                {opt.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="fr-col-12 fr-col-md-3">
          <Input
            label="Créé après le"
            nativeInputProps={{
              type: "date",
              value: query.createdFrom ?? "",
              onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                onChange({
                  createdFrom: e.currentTarget.value || undefined,
                  page: 1,
                }),
            }}
          />
        </div>
        <div className="fr-col-12 fr-col-md-3">
          <Input
            label="Créé avant le"
            nativeInputProps={{
              type: "date",
              value: query.createdTo ?? "",
              onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                onChange({
                  createdTo: e.currentTarget.value || undefined,
                  page: 1,
                }),
            }}
          />
        </div>
        <div className="fr-col-12 fr-col-md-3">
          <Input
            label="Modifié après le"
            nativeInputProps={{
              type: "date",
              value: query.modifiedFrom ?? "",
              onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                onChange({
                  modifiedFrom: e.currentTarget.value || undefined,
                  page: 1,
                }),
            }}
          />
        </div>
        <div className="fr-col-12 fr-col-md-3">
          <Input
            label="Modifié avant le"
            nativeInputProps={{
              type: "date",
              value: query.modifiedTo ?? "",
              onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                onChange({
                  modifiedTo: e.currentTarget.value || undefined,
                  page: 1,
                }),
            }}
          />
        </div>

        <div className="fr-col-12">
          <Button
            priority="secondary"
            onClick={() => onReset?.()}
          >
            Réinitialiser
          </Button>
        </div>
      </div>
    </div>
  );
}
