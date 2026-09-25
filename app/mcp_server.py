from typing import Any

from mcp.server import MCPServer

from app.services.data_service import (
    get_data_range as fetch_data_range,
    get_summary,
)


mcp = MCPServer(
    "AuctionSuit Data MCP"
)


@mcp.tool(
    structured_output=True
)
def get_data_summary() -> dict[str, Any]:
    """
    옥션슈트 전체 데이터의 요약 통계를 조회합니다.

    데이터 기간, 평균값, 최고/최저값,
    최근 추세, 최근 7일과 이전 7일의
    증감률 정보를 반환합니다.
    """

    return get_summary()


@mcp.tool(
    structured_output=True
)
def get_data_range(
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]:
    """
    지정한 기간의 옥션슈트 일별 데이터를 조회합니다.

    start_date와 end_date는
    YYYY-MM-DD 형식을 사용합니다.
    """

    return fetch_data_range(
        start_date=start_date,
        end_date=end_date,
    )