import React from "react";

export type PaginationDsfrProps = Readonly<{
    page: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    maxPageButtons?: number; // total of numeric buttons including current (excluding first/last when far)
    className?: string;
}>;

function clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value));
}

export function PaginationDsfr(props: PaginationDsfrProps): JSX.Element {
    const { page, totalPages, onPageChange, maxPageButtons = 5, className } = props;

    const current = clamp(page, 1, Math.max(1, totalPages));
    const last = Math.max(1, totalPages);

    const windowSize = Math.max(1, Math.min(maxPageButtons, 9));
    const half = Math.floor(windowSize / 2);
    let start = clamp(current - half, 1, Math.max(1, last - windowSize + 1));
    let end = clamp(start + windowSize - 1, 1, last);
    // readjust start when near the end
    start = clamp(end - windowSize + 1, 1, Math.max(1, last - windowSize + 1));

    const pages: Array<number | "ellipsis"> = [];
    const push = (n: number | "ellipsis") => pages.push(n);

    // Always show first
    push(1);
    if (start > 2) push("ellipsis");
    for (let n = Math.max(2, start); n <= Math.min(end, last - 1); n++) push(n);
    if (end < last - 1) push("ellipsis");
    if (last > 1) push(last);

    const go = (n: number) => {
        if (n === current || n < 1 || n > last) return;
        onPageChange(n);
    };

    return (
        <nav className={`fr-pagination${className ? ` ${className}` : ""}`} role="navigation" aria-label="pagination">
            <ul className="fr-pagination__list">
                <li>
                    <a
                        className="fr-pagination__link fr-pagination__link--first"
                        href="#"
                        title="Première page"
                        aria-disabled={current === 1}
                        onClick={e => {
                            e.preventDefault();
                            go(1);
                        }}
                    >
                        Première page
                    </a>
                </li>
                <li>
                    <a
                        className="fr-pagination__link fr-pagination__link--prev"
                        href="#"
                        title="Page précédente"
                        aria-disabled={current === 1}
                        onClick={e => {
                            e.preventDefault();
                            go(current - 1);
                        }}
                    >
                        Page précédente
                    </a>
                </li>
                {pages.map((p, idx) => (
                    <li key={`${p}-${idx}`}>
                        {p === "ellipsis" ? (
                            <a
                                className="fr-pagination__link fr-pagination__link--ellipsis"
                                href="#"
                                title="Aller à une page"
                                onClick={e => {
                                    e.preventDefault();
                                    const raw = window.prompt("Aller à la page :", String(current));
                                    if (!raw) return;
                                    const n = Number.parseInt(raw, 10);
                                    if (Number.isNaN(n)) return;
                                    go(n);
                                }}
                            >
                                …
                            </a>
                        ) : (
                            <a
                                className={`fr-pagination__link${p === current ? " fr-pagination__link--current" : ""}`}
                                href="#"
                                title={`Page ${p}`}
                                aria-current={p === current ? "page" : undefined}
                                onClick={e => {
                                    e.preventDefault();
                                    go(p);
                                }}
                            >
                                {p.toLocaleString("fr-FR")}
                            </a>
                        )}
                    </li>
                ))}
                <li>
                    <a
                        className="fr-pagination__link fr-pagination__link--next"
                        href="#"
                        title="Page suivante"
                        aria-disabled={current === last}
                        onClick={e => {
                            e.preventDefault();
                            go(current + 1);
                        }}
                    >
                        Page suivante
                    </a>
                </li>
                <li>
                    <a
                        className="fr-pagination__link fr-pagination__link--last"
                        href="#"
                        title="Dernière page"
                        aria-disabled={current === last}
                        onClick={e => {
                            e.preventDefault();
                            go(last);
                        }}
                    >
                        Dernière page
                    </a>
                </li>
            </ul>
        </nav>
    );
}


