import plotly.graph_objects as go
import plotly.io as pio


async def generate_chart_html(chart_data: dict, file_path: str) -> None:
    """
    차트 데이터를 기반으로 Plotly 그래프를 생성하고 HTML 파일로 저장합니다.
    여러 개의 trace를 지원하며, 마우스 호버 시 실제 값을 보여주는 기능을 포함합니다.

    Args:
        chart_data (dict): 차트 생성을 위한 데이터.
                           - title: 차트 제목
                           - x_values: X축 값 리스트
                           - traces: 각 trace의 정보가 담긴 리스트.
                             (예: [{'name': '라인1', 'y_values': [100, 102, 98], 'custom_data': [500, 510, 490]}, ...])
        file_path (str): 차트를 저장할 HTML 파일의 경로.
    """
    title = chart_data.get("title", "차트 제목")
    x_values = chart_data.get("x_values", [])
    traces = chart_data.get("traces", [])

    fig = go.Figure()

    for trace in traces:
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=trace.get("y_values", []),
                customdata=trace.get("custom_data", []),
                mode="lines+markers",
                name=trace.get("name", ""),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    + "날짜: %{x}<br>"
                    + "실제 값: %{customdata:,.0f}<extra></extra>"
                ),
            )
        )

    fig.update_layout(title_text=title, legend_title_text="범례")

    pio.write_html(fig, file=file_path, auto_open=False, include_plotlyjs="cdn")
