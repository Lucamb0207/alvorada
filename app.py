import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime
import os
import fetchers

REFRESH_MS = 600_000  # 10 minutes

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "Energy & Markets Dashboard"
server = app.server

# ---------------------------------------------------------------------------
# Shared component builders
# ---------------------------------------------------------------------------

def _card(header_icon: str, header_text: str, body_id: str, body_style=None):
    style = {"maxHeight": "300px", "overflowY": "auto", **(body_style or {})}
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(header_icon, className="me-2"),
                    html.Strong(header_text),
                ],
                className="py-2",
            ),
            dbc.CardBody(
                dcc.Loading(html.Div(id=body_id, style=style), type="circle", color="#0dcaf0"),
                className="p-2",
            ),
        ],
        className="h-100 shadow-sm",
    )


def _news_items(items: list[dict], accent: str = "#0dcaf0") -> html.Div:
    if not items:
        return html.P("Nenhuma notícia disponível.", className="text-muted small")

    children = []
    for item in items:
        children.append(
            html.Div(
                [
                    html.A(
                        item["title"],
                        href=item["link"],
                        target="_blank",
                        className="text-white text-decoration-none",
                        style={"fontSize": "0.82rem", "fontWeight": "500", "lineHeight": "1.3"},
                    ),
                    html.Div(
                        [
                            html.Span(item.get("source", ""), className="text-muted", style={"fontSize": "0.70rem"}),
                            html.Span(" · ", className="text-muted"),
                            html.Span(item.get("time_ago", ""), className="text-muted", style={"fontSize": "0.70rem"}),
                        ]
                    ),
                ],
                style={
                    "borderLeft": f"3px solid {accent}",
                    "paddingLeft": "8px",
                    "marginBottom": "8px",
                },
            )
        )
    return html.Div(children)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

app.layout = dbc.Container(
    fluid=True,
    className="px-3 py-2",
    style={"minHeight": "100vh", "background": "#0f1117"},
    children=[
        # ── Header ─────────────────────────────────────────────────────────
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4(
                            [html.Span("⚡ ", style={"color": "#0dcaf0"}), "Energy & Markets Dashboard"],
                            className="mb-0 text-white",
                        ),
                    ],
                    width="auto",
                ),
                dbc.Col(
                    html.Span(id="last-refresh", className="text-muted", style={"fontSize": "0.78rem"}),
                    className="d-flex align-items-center",
                ),
                dbc.Col(
                    dbc.Badge("Auto-refresh: 10 min", color="info", className="ms-auto"),
                    width="auto",
                    className="d-flex align-items-center",
                ),
            ],
            className="mb-3 align-items-center",
        ),

        # ── Row 1: Venezuela | Global News ─────────────────────────────────
        dbc.Row(
            [
                dbc.Col(_card("🇻🇪", "Notícias Venezuela", "venezuela-news"), md=4, className="mb-3"),
                dbc.Col(_card("🌍", "Monitor de Notícias Globais", "global-news"), md=8, className="mb-3"),
            ]
        ),

        # ── Row 2: O&G News | O&G Events ───────────────────────────────────
        dbc.Row(
            [
                dbc.Col(_card("🛢️", "Monitor de Notícias O&G", "og-news"), md=6, className="mb-3"),
                dbc.Col(_card("📅", "Monitor de Eventos O&G", "og-events"), md=6, className="mb-3"),
            ]
        ),

        # ── Row 3: Brent Chart | OFAC Venezuela ────────────────────────────
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [html.Span("📈  ", className="me-1"), html.Strong("Preço Brent & WTI (30 dias)")],
                                className="py-2",
                            ),
                            dbc.CardBody(
                                dcc.Loading(
                                    dcc.Graph(
                                        id="brent-chart",
                                        config={"displayModeBar": False},
                                        style={"height": "280px"},
                                    ),
                                    type="circle",
                                    color="#0dcaf0",
                                ),
                                className="p-1",
                            ),
                        ],
                        className="h-100 shadow-sm",
                    ),
                    md=8,
                    className="mb-3",
                ),
                dbc.Col(_card("🏛️", "OFAC — Venezuela Sanctions", "ofac-news"), md=4, className="mb-3"),
            ]
        ),

        dcc.Interval(id="interval", interval=REFRESH_MS, n_intervals=0),

        # ── Row 4: Production Chart | KPIs ─────────────────────────────────
        html.Hr(style={"borderColor": "#2a2d3a", "margin": "8px 0"}),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([html.Span("🛢️  ", className="me-1"), html.Strong("Produção Diária — GED-14 (bls)")], className="py-2"),
                    dbc.CardBody(
                        dcc.Loading(dcc.Graph(id="prod-chart", config={"displayModeBar": False}, style={"height": "260px"}), type="circle", color="#0dcaf0"),
                        className="p-1",
                    ),
                ], className="h-100 shadow-sm"),
                md=8, className="mb-3",
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([html.Span("📊  ", className="me-1"), html.Strong("KPIs do Mês")], className="py-2"),
                    dbc.CardBody(dcc.Loading(html.Div(id="prod-kpis"), type="circle", color="#0dcaf0"), className="p-2"),
                ], className="h-100 shadow-sm"),
                md=4, className="mb-3",
            ),
        ]),

        # ── Row 5: Failures ────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(_card("⚠️", "Falhas & Explicações Recentes", "prod-falhas"), md=12, className="mb-3"),
        ]),
    ],
)

# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@app.callback(Output("last-refresh", "children"), Input("interval", "n_intervals"))
def update_timestamp(_):
    return f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"


@app.callback(Output("venezuela-news", "children"), Input("interval", "n_intervals"))
def update_venezuela(_):
    items = fetchers.fetch_news(fetchers.VENEZUELA_FEEDS, max_items=8)
    return _news_items(items, accent="#FFD700")


@app.callback(Output("global-news", "children"), Input("interval", "n_intervals"))
def update_global(_):
    items = fetchers.fetch_news(fetchers.GLOBAL_FEEDS, max_items=10)
    return _news_items(items, accent="#0dcaf0")


@app.callback(Output("og-news", "children"), Input("interval", "n_intervals"))
def update_og_news(_):
    items = fetchers.fetch_news(fetchers.OG_NEWS_FEEDS, max_items=8)
    return _news_items(items, accent="#fd7e14")


@app.callback(Output("og-events", "children"), Input("interval", "n_intervals"))
def update_og_events(_):
    static_events, news_events = fetchers.fetch_og_events()

    # Upcoming conferences section
    conf_items = []
    for ev in static_events:
        conf_items.append(
            html.Div(
                [
                    html.A(
                        ev["name"],
                        href=ev["url"],
                        target="_blank",
                        className="text-white text-decoration-none",
                        style={"fontSize": "0.82rem", "fontWeight": "500"},
                    ),
                    html.Div(
                        [
                            dbc.Badge(ev["date"], color="warning", text_color="dark", className="me-1", style={"fontSize": "0.65rem"}),
                            html.Span(ev["location"], className="text-muted", style={"fontSize": "0.70rem"}),
                        ]
                    ),
                ],
                style={"borderLeft": "3px solid #ffc107", "paddingLeft": "8px", "marginBottom": "8px"},
            )
        )

    # News about events
    news_section = []
    if news_events:
        news_section = [
            html.Hr(className="my-2", style={"borderColor": "#333"}),
            html.P("Notícias de Eventos", className="text-muted mb-1", style={"fontSize": "0.72rem", "textTransform": "uppercase"}),
            *[
                html.Div(
                    [
                        html.A(
                            item["title"],
                            href=item["link"],
                            target="_blank",
                            className="text-white text-decoration-none",
                            style={"fontSize": "0.80rem"},
                        ),
                        html.Div(
                            html.Span(item.get("time_ago", ""), className="text-muted", style={"fontSize": "0.68rem"})
                        ),
                    ],
                    style={"borderLeft": "3px solid #6f42c1", "paddingLeft": "8px", "marginBottom": "6px"},
                )
                for item in news_events
            ],
        ]

    return html.Div(conf_items + news_section)


@app.callback(Output("brent-chart", "figure"), Input("interval", "n_intervals"))
def update_brent(_):
    brent_close, brent_price, brent_pct, wti_close, wti_price, wti_pct = fetchers.fetch_oil_prices()

    fig = go.Figure()

    if brent_close.empty and wti_close.empty:
        fig.add_annotation(text="Dados não disponíveis", x=0.5, y=0.5, showarrow=False, font=dict(color="#aaa"))
        fig.update_layout(**_dark_layout())
        return fig

    brent_color = "#64b5f6"
    wti_color   = "#FFD600"

    if not brent_close.empty:
        fig.add_trace(go.Scatter(
            x=brent_close.index.tolist(), y=brent_close.tolist(),
            mode="lines", name="Brent",
            line=dict(color=brent_color, width=2),
            hovertemplate="%{x|%d/%m}<br>Brent US$ %{y:.2f}<extra></extra>",
        ))

    if not wti_close.empty:
        fig.add_trace(go.Scatter(
            x=wti_close.index.tolist(), y=wti_close.tolist(),
            mode="lines", name="WTI",
            line=dict(color=wti_color, width=2),
            hovertemplate="%{x|%d/%m}<br>WTI US$ %{y:.2f}<extra></extra>",
        ))

    annotations = []
    if brent_price:
        arrow = "▲" if brent_pct >= 0 else "▼"
        annotations.append(dict(
            text=f"Brent  US$ {brent_price:.2f}  {arrow} {abs(brent_pct):.2f}%",
            xref="paper", yref="paper", x=0.01, y=0.97,
            showarrow=False, font=dict(size=13, color=brent_color), align="left",
        ))
    if wti_price:
        arrow = "▲" if wti_pct >= 0 else "▼"
        annotations.append(dict(
            text=f"WTI     US$ {wti_price:.2f}  {arrow} {abs(wti_pct):.2f}%",
            xref="paper", yref="paper", x=0.01, y=0.82,
            showarrow=False, font=dict(size=13, color=wti_color), align="left",
        ))

    fig.update_layout(
        **_dark_layout(),
        margin=dict(l=10, r=10, t=10, b=30),
        annotations=annotations,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=1.05, font=dict(size=10, color="#ccc")),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#888"), tickformat="%d/%m"),
        yaxis=dict(showgrid=True, gridcolor="#1e2130", tickfont=dict(size=10, color="#888"), tickprefix="$"),
    )
    return fig


@app.callback(Output("ofac-news", "children"), Input("interval", "n_intervals"))
def update_ofac(_):
    items = fetchers.fetch_news(fetchers.OFAC_FEEDS, max_items=10)
    return _news_items(items, accent="#dc3545")


@app.callback(
    Output("prod-chart", "figure"),
    Output("prod-kpis", "children"),
    Output("prod-falhas", "children"),
    Input("interval", "n_intervals"),
)
def update_producao(_):
    rows = fetchers.fetch_producao(days=60)

    empty_fig = go.Figure()
    empty_fig.add_annotation(text="Sem dados — rode parse_report.py para alimentar", x=0.5, y=0.5, showarrow=False, font=dict(color="#888", size=12))
    empty_fig.update_layout(**_dark_layout(), margin=dict(l=10, r=10, t=10, b=10))

    if not rows:
        return (
            empty_fig,
            html.P("Sem dados de produção ainda.", className="text-muted small"),
            html.P("Sem falhas registradas.", className="text-muted small"),
        )

    fecha_vals = [r["fecha"] for r in rows]
    dates = [d.strftime("%d/%m") if hasattr(d, "strftime") else str(d) for d in fecha_vals]
    pb    = [r.get("pb_bls") for r in rows]
    pn    = [r.get("pn_bls") for r in rows]

    # Use most recent non-null values for the horizontal reference lines
    pdt_val  = next((r["pdt_plan"]         for r in reversed(rows) if r.get("pdt_plan")),         None)
    prom_val = next((r["prom_mes_operada"] for r in reversed(rows) if r.get("prom_mes_operada")), None)

    fig = go.Figure()

    # PB Bruto bars — azul escuro
    fig.add_trace(go.Bar(
        x=dates, y=pb, name="PB Bruto",
        marker_color="#0d2b6e",
        text=pb, textposition="outside",
        textfont=dict(size=10, color="#e0e0e0"),
        hovertemplate="%{x|%d/%m}<br>PB Bruto: %{y} bls<extra></extra>",
    ))

    # PB Neto bars — amarelo
    fig.add_trace(go.Bar(
        x=dates, y=pn, name="PB Neto",
        marker_color="#FFD600",
        text=pn, textposition="outside",
        textfont=dict(size=10, color="#e0e0e0"),
        hovertemplate="%{x|%d/%m}<br>PB Neto: %{y} bls<extra></extra>",
    ))

    # Linha PDT — azul claro horizontal
    if pdt_val:
        fig.add_hline(
            y=pdt_val, line_color="#90caf9", line_width=2,
            annotation_text=f"PDT {pdt_val:,}".replace(",", "."),
            annotation_font=dict(color="#90caf9", size=10),
            annotation_position="top right",
        )

    # Linha Prom Mês — cinza claro horizontal
    if prom_val:
        fig.add_hline(
            y=prom_val, line_color="#cfd8dc", line_width=2,
            annotation_text=f"Prom Mês {prom_val:,}".replace(",", "."),
            annotation_font=dict(color="#cfd8dc", size=10),
            annotation_position="bottom right",
        )

    # Adicionar entradas de legenda para as linhas horizontais
    if pdt_val:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="PDT",
                                 line=dict(color="#90caf9", width=2)))
    if prom_val:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Prom Mês",
                                 line=dict(color="#cfd8dc", width=2)))

    yvals = [v for v in pb + pn if v] + ([pdt_val] if pdt_val else []) + ([prom_val] if prom_val else [])
    y_min = min(yvals) * 0.96 if yvals else 0
    y_max = max(yvals) * 1.08 if yvals else 100

    fig.update_layout(
        **_dark_layout(),
        title=dict(text="Produção", font=dict(size=14, color="#ccc"), x=0.5),
        margin=dict(l=10, r=80, t=40, b=30),
        legend=dict(orientation="h", x=0, y=1.12, font=dict(size=10, color="#ccc")),
        xaxis=dict(type="category", showgrid=False, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor="#1e2130", tickfont=dict(size=10, color="#888"),
                   range=[y_min, y_max]),
        showlegend=True,
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
    )

    # KPIs from last row
    last = rows[-1]
    def _kpi(label, value, unit="bls", good=None):
        if value is None:
            return html.Div([html.Span(label + ": ", className="text-muted", style={"fontSize":"0.75rem"}),
                             html.Span("—", className="text-muted")], className="mb-2")
        color = "#e0e0e0"
        if good is not None:
            color = "#00e676" if good else "#ff5252"
        return html.Div([
            html.Div(label, className="text-muted", style={"fontSize": "0.70rem"}),
            html.Div(f"{value:,} {unit}".replace(",", "."), style={"fontSize": "1.1rem", "fontWeight": "bold", "color": color}),
        ], className="mb-2", style={"borderLeft": "3px solid #333", "paddingLeft": "8px"})

    pn_last = last.get("pn_bls")
    pdt_last = last.get("pdt_plan")
    var = last.get("var_vs_pdt")
    op = last.get("prom_mes_operada")
    fisc = last.get("prom_mes_fiscalizada")

    kpis = html.Div([
        html.P(str(last["fecha"].strftime("%d/%m/%Y")), className="text-muted mb-2", style={"fontSize":"0.72rem"}),
        _kpi("PN Dia", pn_last, good=(pn_last >= pdt_last if pn_last and pdt_last else None)),
        _kpi("PDT Plan", pdt_last),
        _kpi("Var vs PDT", var, good=(var >= 0 if var is not None else None)),
        _kpi("Prom Mês Operada", op, good=(op >= pdt_last if op and pdt_last else None)),
        _kpi("Prom Mês Fiscalizada", fisc),
    ])

    # Failures panel — last 5 days with falhas
    falha_rows = [r for r in reversed(rows) if r.get("falhas")][:5]
    if not falha_rows:
        falhas_div = html.P("Nenhuma falha registrada.", className="text-muted small")
    else:
        items = []
        for r in falha_rows:
            bullets = r["falhas"].splitlines()
            items.append(html.Div([
                html.Span(r["fecha"].strftime("%d/%m/%Y"), className="text-muted me-2", style={"fontSize":"0.70rem"}),
                *[html.Div("• " + b, style={"fontSize": "0.78rem", "color": "#e0e0e0", "marginLeft": "8px"}) for b in bullets],
            ], style={"borderLeft": "3px solid #fd7e14", "paddingLeft": "8px", "marginBottom": "10px"}))
        falhas_div = html.Div(items)

    return fig, kpis, falhas_div


# ---------------------------------------------------------------------------
# Dark layout template
# ---------------------------------------------------------------------------

def _dark_layout() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ccc"),
        showlegend=False,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DASH_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
