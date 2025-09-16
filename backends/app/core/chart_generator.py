
import plotly.graph_objects as go

async def generate_chart_html(chart_data: dict) -> str:
    """
    차트 데이터를 기반으로 Plotly 그래프를 생성하고 완전한 HTML 문자열로 반환합니다.
    여러 개의 trace를 지원하며, 마우스 호버 시 실제 값을 보여주는 기능을 포함합니다.

    Args:
        chart_data (dict): 차트 생성을 위한 데이터.
                           - title: 차트 제목
                           - x_values: X축 값 리스트
                           - traces: 각 trace의 정보가 담긴 리스트.
                             (예: [{
                                 'name': '라인1', 
                                 'y_values': [100, 102, 98],  # 정규화된 값
                                 'custom_data': [500, 510, 490] # 실제 값
                             }, ...])
    Returns:
        str: 독립적으로 실행 가능한 HTML 형식의 차트 코드
    """
    title = chart_data.get("title", "차트 제목")
    x_values = chart_data.get("x_values", [])
    traces = chart_data.get("traces", [])

    fig = go.Figure()

    for trace in traces:
        fig.add_trace(go.Scatter(
            x=x_values,
            y=trace.get('y_values', []),
            customdata=trace.get('custom_data', []),
            mode='lines+markers',
            name=trace.get('name', ''),
            hovertemplate=(
                '<b>%{fullData.name}</b><br>' +
                '날짜: %{x}<br>' +
                '실제 값: %{customdata:,.0f}<extra></extra>' # 포맷 지정: 천 단위 콤마, 소수점 없음
            )
        ))

    fig.update_layout(
        title_text=title,
        legend_title_text='범례'
    )

    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    return chart_html
