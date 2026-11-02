"""Genera dashboard/dashboard.html a partir de data/tickets_anonimizados.csv.
Uso (desde la raíz del repositorio): python scripts/crear_dashboard.py"""
import pandas as pd
import plotly.graph_objects as go

AZUL, TEXTO, TEXTO2, GRID = '#2a78d6', '#0b0b0b', '#52514e', '#e4e3df'
t = pd.read_csv('data/tickets_anonimizados.csv', parse_dates=['registrado', 'resuelto'])
t['minutos'] = (t['resuelto'] - t['registrado']).dt.total_seconds() / 60
v = t[(t['estatus'] == 'Resuelto') & (t['minutos'] >= 0)]

kpis = [
    (f"{len(t)}", "tickets en el primer mes"),
    (f"{v['minutos'].median():.0f} min", "tiempo mediano de resolución"),
    (f"{(v['minutos'] <= 60).mean():.0%}", "resueltos en menos de 1 hora"),
    (f"{(t['tipo_formulario'] == 'Otro').mean():.0%}", "registrados como “Otro” en el formulario"),
]

def layout(fig, titulo, alto=360):
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=15, color=TEXTO)), height=alto,
                      margin=dict(l=10, r=30, t=50, b=10), plot_bgcolor='white', paper_bgcolor='white',
                      font=dict(family='Inter, system-ui, sans-serif', color=TEXTO2, size=12),
                      hoverlabel=dict(bgcolor='white', font_color=TEXTO))
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(showgrid=False)
    return fig

def barras(serie, titulo, sufijo='', hover='Tickets'):
    s = serie.sort_values()
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation='h', marker_color=AZUL,
                           text=[f'{x:g}{sufijo}' for x in s.values], textposition='outside',
                           cliponaxis=False,
                           hovertemplate='%{y}<br>' + hover + ': %{x}' + sufijo + '<extra></extra>'))
    fig = layout(fig, titulo, 70 + 34 * len(s))
    fig.update_xaxes(range=[0, s.max() * 1.2])   # espacio para las etiquetas
    return fig

figs = []
figs.append(barras(t['tema'].value_counts(), 'Tickets por tema'))
med = v.groupby('tema')['minutos'].agg(['median', 'count'])
figs.append(barras(med[med['count'] >= 5]['median'].round(0), 'Tiempo mediano de resolución por tema (temas con 5+ tickets)', ' min', 'Mediana'))
figs.append(barras(t['area'].value_counts(), 'Tickets por área'))
figs.append(barras((t['tipo_formulario'].value_counts(normalize=True) * 100).round(1), 'Categoría elegida en el formulario', '%', 'Porcentaje'))
hora = t['registrado'].dt.hour.value_counts().sort_index()
f = go.Figure(go.Bar(x=[f'{h}:00' for h in hora.index], y=hora.values, marker_color=AZUL,
                     hovertemplate='%{x}<br>Tickets: %{y}<extra></extra>'))
f = layout(f, 'Tickets por hora de registro'); f.update_xaxes(showgrid=False); f.update_yaxes(showgrid=True, gridcolor=GRID)
figs.append(f)

# La primera gráfica incluye la librería Plotly completa: así el archivo funciona sin internet
divs = [fig.to_html(full_html=False, include_plotlyjs=(i == 0), config={'displayModeBar': False}) for i, fig in enumerate(figs)]
tiles = ''.join(f'<div class="kpi"><div class="v">{a}</div><div class="l">{b}</div></div>' for a, b in kpis)
cards = ''.join(f'<div class="card">{d}</div>' for d in divs)
html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAASCANET · Dashboard de soporte</title>
<style>
body{{margin:0;background:#f7f8fa;color:{TEXTO};font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:28px 16px}}
h1{{font-size:26px;margin:0 0 6px}} .sub{{color:{TEXTO2};margin:0 0 22px;line-height:1.5}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}}
.kpi{{background:#fff;border:1px solid #e3e6ec;border-radius:12px;padding:16px 18px}}
.kpi .v{{font-size:28px;font-weight:700}} .kpi .l{{color:{TEXTO2};font-size:13px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.card{{background:#fff;border:1px solid #e3e6ec;border-radius:12px;padding:8px 12px;min-width:0}}
@media (max-width:800px){{.grid{{grid-template-columns:1fr}}}}
footer{{color:{TEXTO2};font-size:13px;margin-top:20px}}
</style></head><body><div class="wrap">
<h1>Soporte técnico en SAASCANET · primer mes</h1>
<p class="sub">Tickets del {t['registrado'].min():%d/%m/%Y} al {t['registrado'].max():%d/%m/%Y}. Datos anonimizados. Pasa el cursor sobre las barras para ver el detalle.</p>
<div class="kpis">{tiles}</div>
<div class="grid">{cards}</div>
<footer>Análisis de Luis Antonio Hernández Ruiz · Código: github.com/LAHRZ23/saascanet-analisis-soporte</footer>
</div></body></html>"""
open('dashboard/dashboard.html', 'w', encoding='utf-8').write(html)
print('dashboard/dashboard.html generado')
