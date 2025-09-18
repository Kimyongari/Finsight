import plotly.graph_objects as go
import plotly.io as pio


async def generate_chart_html(chart_data: dict, file_path: str) -> None:
    """
    차트 데이터를 기반으로 Plotly 그래프를 생성하고 HTML 파일로 저장합니다.
    선그래프, 막대그래프, 듀얼차트(토글 가능)를 지원하며, 마우스 호버 시 상세 정보를 보여줍니다.

    Args:
        chart_data (dict): 차트 생성을 위한 데이터.
                           - title: 차트 제목
                           - x_values: X축 값 리스트 (단일 차트용)
                           - traces: 각 trace의 정보가 담긴 리스트 (단일 차트용)
                           - chart_type: 'line' (기본값), 'bar', 또는 'dual'
                           - bar_data: 막대그래프 데이터 (dual용)
                           - line_data: 선그래프 데이터 (dual용)
        file_path (str): 차트를 저장할 HTML 파일의 경로.
    """
    title = chart_data.get("title", "차트 제목")
    chart_type = chart_data.get("chart_type", "line")

    fig = go.Figure()

    if chart_type == "dual":
        # 듀얼 차트: 막대그래프와 선그래프를 토글 버튼으로 전환
        bar_data = chart_data.get("bar_data", {})
        line_data = chart_data.get("line_data", {})

        # 막대그래프 traces 추가 (초기 visible=True)
        _add_bar_traces(fig, bar_data, visible=True, name_prefix="bar_")

        # 선그래프 traces 추가 (초기 visible=False)
        _add_line_traces(fig, line_data, visible=False, name_prefix="line_")

        # 토글 버튼 설정
        updatemenus = [{
            "buttons": [
                {
                    "label": "전년대비 증감률",
                    "method": "update",
                    "args": [
                        {"visible": [True] * len(bar_data.get("traces", [])) + [False] * len(line_data.get("traces", []))},
                        {
                            "yaxis.title": "증감률 (%)",
                            "xaxis.title": "재무 지표"
                        }
                    ]
                },
                {
                    "label": "기간별 비교",
                    "method": "update",
                    "args": [
                        {"visible": [False] * len(bar_data.get("traces", [])) + [True] * len(line_data.get("traces", []))},
                        {
                            "yaxis.title": "값 (억원)",
                            "xaxis.title": "기간"
                        }
                    ]
                }
            ],
            "direction": "down",
            "showactive": True,
            "x": 1.0,
            "xanchor": "right",
            "y": 1.02,
            "yanchor": "bottom"
        }]

        layout_updates = {
            "title_text": title,
            "legend_title_text": "범례",
            "updatemenus": updatemenus,
            "yaxis_title": "증감률 (%)",
            "xaxis_title": "재무 지표"
        }

    elif chart_type == "profitability":
        # 수익성 차트 로직
        x_values = chart_data.get("x_values", [])
        traces = chart_data.get("traces", [])

        for trace in traces:
            trace_name = trace.get("name", "")
            y_values = trace.get("y_values", [])
            custom_data = trace.get("custom_data", [])
            _add_profitability_line_trace(fig, x_values, trace_name, y_values, custom_data)

        # 수익성 차트 전용 레이아웃 설정
        layout_updates = {
            "title_text": title,
            "legend_title_text": "수익성 지표",
            "yaxis_title": "이익률 (%)",
            "xaxis_title": "기간"
        }

    else:
        # 기존 단일 차트 로직
        x_values = chart_data.get("x_values", [])
        traces = chart_data.get("traces", [])

        for trace in traces:
            trace_name = trace.get("name", "")
            y_values = trace.get("y_values", [])
            custom_data = trace.get("custom_data", [])

            if chart_type == "bar":
                _add_single_bar_trace(fig, x_values, trace_name, y_values, custom_data)
            else:
                _add_single_line_trace(fig, x_values, trace_name, y_values, custom_data)

        # 레이아웃 설정
        layout_updates = {"title_text": title, "legend_title_text": "범례"}

        if chart_type == "bar":
            layout_updates.update({
                "yaxis_title": "증감률 (%)",
                "xaxis_title": "재무 지표"
            })

    fig.update_layout(**layout_updates)
    pio.write_html(fig, file=file_path, auto_open=False, include_plotlyjs="cdn")


def _add_bar_traces(fig: go.Figure, bar_data: dict, visible: bool = True, name_prefix: str = ""):
    """막대그래프 traces를 Figure에 추가합니다."""
    x_values = bar_data.get("x_values", [])
    traces = bar_data.get("traces", [])

    for trace in traces:
        trace_name = f"{name_prefix}{trace.get('name', '')}"
        y_values = trace.get("y_values", [])
        custom_data = trace.get("custom_data", [])

        # 증감률 차트용 호버 템플릿
        if isinstance(custom_data, list) and len(custom_data) > 0 and isinstance(custom_data[0], dict):
            # 단위 정보가 포함된 상세 호버
            if "unit" in custom_data[0]:
                hovertemplate = (
                    "<b>%{x}</b><br>"
                    + "증감률: %{y}%<br>"
                    + "%{customdata.base_period}: %{customdata.base:,.0f} %{customdata.unit}<br>"
                    + "%{customdata.current_period}: %{customdata.current:,.0f} %{customdata.unit}<br>"
                    + "<extra></extra>"
                )
            else:
                hovertemplate = (
                    "<b>%{x}</b><br>"
                    + "증감률: %{y}%<br>"
                    + "%{customdata.base_period}: %{customdata.base:,.0f}<br>"
                    + "%{customdata.current_period}: %{customdata.current:,.0f}<br>"
                    + "<extra></extra>"
                )
            text = [f"{val}%" for val in y_values]
        else:
            hovertemplate = (
                "<b>%{x}</b><br>"
                + "값: %{y:,.1f}<br>"
                + "<extra></extra>"
            )
            text = [f"{val}" for val in y_values]

        fig.add_trace(
            go.Bar(
                x=x_values,
                y=y_values,
                customdata=custom_data,
                name=trace_name,
                hovertemplate=hovertemplate,
                text=text,
                textposition='outside',
                visible=visible
            )
        )


def _add_line_traces(fig: go.Figure, line_data: dict, visible: bool = True, name_prefix: str = ""):
    """선그래프 traces를 Figure에 추가합니다."""
    x_values = line_data.get("x_values", [])
    traces = line_data.get("traces", [])

    for trace in traces:
        trace_name = f"{name_prefix}{trace.get('name', '')}"
        y_values = trace.get("y_values", [])
        custom_data = trace.get("custom_data", [])

        # custom_data 타입에 따라 호버 템플릿 조정
        if isinstance(custom_data, list) and len(custom_data) > 0 and isinstance(custom_data[0], dict):
            # 단위 정보가 포함된 개선된 호버
            if "original_unit" in custom_data[0] and "display_unit" in custom_data[0]:
                hovertemplate = (
                    "<b>%{fullData.name}</b><br>"
                    + "기간: %{x}<br>"
                    + "값: %{y:,.1f} %{customdata.display_unit}<br>"
                    + "원본값: %{customdata.original:,.0f} %{customdata.original_unit}<extra></extra>"
                )
            else:
                hovertemplate = (
                    "<b>%{fullData.name}</b><br>"
                    + "기간: %{x}<br>"
                    + "값: %{y:,.1f}<br>"
                    + "상세: %{customdata.original:,.0f} 백만원<extra></extra>"
                )
        else:
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
                visible=visible
            )
        )


def _add_single_bar_trace(fig: go.Figure, x_values: list, trace_name: str, y_values: list, custom_data: list):
    """단일 막대그래프 trace를 추가합니다."""
    if isinstance(custom_data, list) and len(custom_data) > 0 and isinstance(custom_data[0], dict):
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


def _add_single_line_trace(fig: go.Figure, x_values: list, trace_name: str, y_values: list, custom_data: list):
    """단일 선그래프 trace를 추가합니다."""
    if isinstance(custom_data, list) and len(custom_data) > 0 and isinstance(custom_data[0], dict):
        hovertemplate = (
            "<b>%{fullData.name}</b><br>"
            + "기간: %{x}<br>"
            + "값: %{y:,.1f}<br>"
            + "상세: %{customdata.original:,.0f} 백만원<extra></extra>"
        )
    else:
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


def _add_profitability_line_trace(fig: go.Figure, x_values: list, trace_name: str, y_values: list, custom_data: list):
    """수익성 지표 선그래프 trace를 추가합니다."""
    if isinstance(custom_data, list) and len(custom_data) > 0 and isinstance(custom_data[0], dict):
        # 수익성 지표 전용 호버 템플릿
        hovertemplate = (
            "<b>%{fullData.name}</b><br>"
            + "기간: %{x}<br>"
            + "비율: %{y:.1f}%<br>"
            + "매출액: %{customdata.revenue:,.0f} 백만원<br>"
            + "해당 이익: %{customdata.profit:,.0f} 백만원<br>"
            + "<extra></extra>"
        )
    else:
        # 기본 호버 템플릿
        hovertemplate = (
            "<b>%{fullData.name}</b><br>"
            + "기간: %{x}<br>"
            + "비율: %{y:.1f}%<br>"
            + "<extra></extra>"
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
