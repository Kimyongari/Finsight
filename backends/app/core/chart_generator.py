import plotly.graph_objects as go
import plotly.io as pio


async def generate_chart_html(chart_data: dict, file_path: str) -> None:
    """
    차트 데이터를 기반으로 Plotly 그래프를 생성하고 HTML 파일로 저장합니다.
    선그래프와 막대그래프를 지원하며, 마우스 호버 시 상세 정보를 보여줍니다.

    Args:
        chart_data (dict): 차트 생성을 위한 데이터.
                           - title: 차트 제목
                           - x_values: X축 값 리스트
                           - traces: 각 trace의 정보가 담긴 리스트
                           - chart_type: 'line' (기본값) 또는 'bar'
        file_path (str): 차트를 저장할 HTML 파일의 경로.
    """
    title = chart_data.get("title", "차트 제목")
    x_values = chart_data.get("x_values", [])
    traces = chart_data.get("traces", [])
    chart_type = chart_data.get("chart_type", "line")

    fig = go.Figure()

    for trace in traces:
        trace_name = trace.get("name", "")
        y_values = trace.get("y_values", [])
        custom_data = trace.get("custom_data", [])

        if chart_type == "bar":
            # 막대그래프용 호버 템플릿
            if isinstance(custom_data, list) and len(custom_data) > 0 and isinstance(custom_data[0], dict):
                # 증감률 차트용 상세 정보
                hovertemplate = (
                    "<b>%{x}</b><br>"
                    + "증감률: %{y}%<br>"
                    + "%{customdata.base_period}: %{customdata.base:,.0f}<br>"
                    + "%{customdata.current_period}: %{customdata.current:,.0f}<br>"
                    + "<extra></extra>"
                )
            else:
                hovertemplate = (
                    "<b>%{x}</b><br>"
                    + "값: %{y:,.1f}<br>"
                    + "<extra></extra>"
                )

            fig.add_trace(
                go.Bar(
                    x=x_values,
                    y=y_values,
                    customdata=custom_data,
                    name=trace_name,
                    hovertemplate=hovertemplate,
                    text=[f"{val}%" for val in y_values],
                    textposition='outside'
                )
            )
        else:
            # 선그래프 (기존 로직)
            # custom_data 타입에 따라 호버 템플릿 조정
            if isinstance(custom_data, list) and len(custom_data) > 0 and isinstance(custom_data[0], dict):
                # 단위 변환된 데이터용
                hovertemplate = (
                    "<b>%{fullData.name}</b><br>"
                    + "기간: %{x}<br>"
                    + "값: %{y:,.1f}<br>"
                    + "상세: %{customdata.original:,.0f} 백만원<extra></extra>"
                )
            else:
                # 기존 방식
                hovertemplate = (
                    "<b>%{fullData.name}</b><br>"
                    + "날짜: %{x}<br>"
                    + "실제 값: %{customdata:,.0f}<extra></extra>"
                )

            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    customdata=custom_data,
                    mode="lines+markers",
                    name=trace_name,
                    hovertemplate=hovertemplate,
                )
            )

    # 레이아웃 설정
    layout_updates = {"title_text": title, "legend_title_text": "범례"}

    if chart_type == "bar":
        layout_updates.update({
            "yaxis_title": "증감률 (%)",
            "xaxis_title": "재무 지표"
        })

    fig.update_layout(**layout_updates)

    pio.write_html(fig, file=file_path, auto_open=False, include_plotlyjs="cdn")
