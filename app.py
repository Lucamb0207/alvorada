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
                                [html.Span("📈  ", className="me-1"), html.Strong("Preço Brent Crude (30 dias)")],
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
    df, current, pct = fetchers.fetch_brent()

    if df.empty or len(df) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Dados não disponíveis", x=0.5, y=0.5, showarrow=False, font=dict(color="#aaa"))
        fig.update_layout(**_dark_layout())
        return fig

    dates = df.index.tolist()
    closes = df.tolist()

    color = "#00e676" if pct >= 0 else "#ff5252"
    fillcolor = "rgba(0,230,118,0.08)" if pct >= 0 else "rgba(255,82,82,0.08)"
    arrow = "▲" if pct >= 0 else "▼"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=closes,
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=fillcolor,
            hovertemplate="%{x|%d/%m}<br>US$ %{y:.2f}<extra></extra>",
        )
    )

    fig.add_annotation(
        text=f"US$ {current:.2f}  {arrow} {abs(pct):.2f}%",
        xref="paper", yref="paper",
        x=0.01, y=0.95,
        showarrow=False,
        font=dict(size=16, color=color),
        align="left",
    )

    fig.update_layout(
        **_dark_layout(),
        margin=dict(l=10, r=10, t=10, b=30),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color="#888"),
            tickformat="%d/%m",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1e2130",
            tickfont=dict(size=10, color="#888"),
            tickprefix="$",
        ),
    )
    return fig


@app.callback(Output("ofac-news", "children"), Input("interval", "n_intervals"))
def update_ofac(_):
    items = fetchers.fetch_news(fetchers.OFAC_FEEDS, max_items=10)
    return _news_items(items, accent="#dc3545")


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
