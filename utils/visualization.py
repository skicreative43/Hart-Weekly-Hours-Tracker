import plotly.graph_objects as go
from io import BytesIO
import pandas as pd


def create_weekly_chart(totals_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=totals_df["Week"], y=totals_df["Estimated Hours"], name="Estimated", marker_color='lightgray'))
    fig.add_trace(go.Bar(x=totals_df["Week"], y=totals_df["Actual Hours"], name="Actual", marker_color='steelblue', opacity=0.56))
    for _, row in totals_df.iterrows():
        if row["Actual Hours"] > 0:
            fig.add_annotation(
                x=row["Week"],
                y=max(row["Estimated Hours"], row["Actual Hours"]) + 10,
                text=f"{row['Difference']}",
                showarrow=False,
                font=dict(size=10),
                yanchor="bottom",
            )
    fig.update_layout(barmode='overlay', title='Estimated vs Actual Hours per Week', xaxis_title='Week', yaxis_title='Hours')
    return fig


def _project_table_html(project_df: pd.DataFrame) -> str:
    cols = [
        "Project Full Name",
        "Current Budget Hours",
        "Actual Hours",
        "Remaining",
    ]
    df = project_df.copy()
    for c in ["Current Budget Hours", "Actual Hours", "Remaining"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        else:
            df[c] = 0.0
    if "Project Full Name" not in df.columns:
        df["Project Full Name"] = "(Unnamed)"

    df = df[cols].sort_values("Project Full Name", kind="stable").reset_index(drop=True)

    total_budget = df["Current Budget Hours"].sum()
    total_actual = df["Actual Hours"].sum()
    total_remaining = df["Remaining"].sum()

    html = [
        "<table class='proj-mini'>",
        "<thead><tr>"
        "<th style='text-align:left'>Project</th>"
        "<th style='text-align:right'>Budget</th>"
        "<th style='text-align:right'>Actual</th>"
        "<th style='text-align:right'>Remaining</th>"
        "</tr></thead>",
        "<tbody>",
    ]

    for _, r in df.iterrows():
        html.append(
            f"<tr>"
            f"<td style='text-align:left'>{r['Project Full Name']}</td>"
            f"<td style='text-align:right'>{r['Current Budget Hours']:,.1f}</td>"
            f"<td style='text-align:right'>{r['Actual Hours']:,.1f}</td>"
            f"<td style='text-align:right'>{r['Remaining']:,.1f}</td>"
            f"</tr>"
        )

    html.append(
        f"<tr class='total'>"
        f"<td style='text-align:left'><strong>Total</strong></td>"
        f"<td style='text-align:right'><strong>{total_budget:,.1f}</strong></td>"
        f"<td style='text-align:right'><strong>{total_actual:,.1f}</strong></td>"
        f"<td style='text-align:right'><strong>{total_remaining:,.1f}</strong></td>"
        f"</tr>"
    )

    html.append("</tbody></table>")
    return "".join(html)


def build_recap_html(grand_est, grand_act, as_of_est, as_of_act, as_of_pct, today, project_df=None):
    # Left: original recap blocks
    left = f"""
    <h3>📊 Grand Total Hours</h2>
    <ul>
    <li><strong>Estimated Hours:</strong> {grand_est:,.0f}</li>
    <li><strong>Actual Hours:</strong> {grand_act:,.2f}</li>
    </ul>
    <h3>📅 As of Today Summary ({today.date()})</h3>
    <ul>
    <li><strong>Estimated Hours:</strong> {as_of_est:,.0f}</li>
    <li><strong>Actual Hours:</strong> {as_of_act:,.2f}</li>
    <li><strong>% of Estimated Hours Used:</strong> {as_of_pct}%</li>
    </ul>
    """

    # Right: mini table of projects from baseline, sorted A→Z, with totals
    right = ""
    if project_df is not None and len(project_df) > 0:
        right = "<h3>📁 Project Breakdown</h3>" + _project_table_html(project_df)

    # Wrap side-by-side using flexbox; on small screens it will stack
    html = f"""
    <style>
    /* Layout */
    /* Center the entire recap area */
    .recap-container {{ width: 90%; margin: 0 auto; }}
    .recap-wrap {{ display: flex; gap: 24px; align-items: flex-start; flex-wrap: wrap; }}
    .recap-left {{ flex: 1 1 320px; min-width: 280px; }}
    .recap-right {{ flex: 1 1 380px; min-width: 320px; }}

    /* Table base styles */
    table.proj-mini {{ border-collapse: collapse; width: 100%; }}
    table.proj-mini th, table.proj-mini td {{ border: 1px solid #ddd; padding: 6px 8px; font-size: 0.95rem; }}
    table.proj-mini thead th {{ background:#f7f7f7; color:#111 !important; }}
    table.proj-mini tr.total td {{ background:#fafafa; border-top: 2px solid #ccc; color:#111 !important; }}

    /* Ensure good contrast when user is in dark mode */
    @media (prefers-color-scheme: dark) {{
        /* Force high-contrast for the project table */
        .recap-right table.proj-mini th,
        .recap-right table.proj-mini td {{
        background:#ffffff !important;
        color:#111 !important;
        }}
        /* Optional: keep borders subtle on white cells */
        .recap-right table.proj-mini th, .recap-right table.proj-mini td {{ border-color: #ddd !important; }}
    }}
    </style>
    <div class=\"recap-container\">
    <div class=\"recap-wrap\">
        <div class=\"recap-left\">{left}</div>
        <div class=\"recap-right\">{right}</div>
    </div>
    </div>
    """
    return html


def export_html(fig, recap_html):
    buffer = BytesIO()
    # Add global CSS to ensure sans-serif fonts in recap section when downloaded
    global_css = (
        "<style>"
        ".recap-wrap, .recap-wrap * {"
        "  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, 'Noto Sans', 'Liberation Sans', sans-serif;"
        "}"
        "</style>"
    )
    full_html = (
        "<html><head><meta charset='utf-8'>" + global_css + "</head><body>" +
        fig.to_html(include_plotlyjs='cdn') + "<hr>" + recap_html +
        "</body></html>"
    )
    buffer.write(full_html.encode("utf-8"))
    return buffer.getvalue()
