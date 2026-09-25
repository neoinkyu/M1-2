import asyncio
import json

from mcp import Client


MCP_URL = "http://127.0.0.1:8000/mcp"


async def main():

    print("MCP 서버 연결 테스트")
    print("URL:", MCP_URL)
    print()

    async with Client(MCP_URL) as client:

        print("연결 성공")
        print(
            "Protocol:",
            client.protocol_version,
        )
        print()

        # ==================================================
        # 1. 등록된 도구 목록 확인
        # ==================================================

        tools_result = (
            await client.list_tools()
        )

        print("등록된 MCP 도구:")

        for tool in tools_result.tools:
            print(
                f"- {tool.name}"
            )

        print()


        # ==================================================
        # 2. 전체 데이터 요약 도구 호출
        # ==================================================

        print(
            "[get_data_summary 호출]"
        )

        summary_result = (
            await client.call_tool(
                "get_data_summary",
                {},
            )
        )

        print(
            "is_error:",
            summary_result.is_error,
        )

        print(
            "structured_content:"
        )

        print(
            json.dumps(
                summary_result.structured_content,
                ensure_ascii=False,
                indent=2,
            )
        )

        print(
            "content:"
        )

        for item in summary_result.content:
            print(item)

        print()


        # ==================================================
        # 3. 특정 기간 데이터 조회 도구 호출
        # ==================================================

        print(
            "[get_data_range 호출]"
        )

        range_result = (
            await client.call_tool(
                "get_data_range",
                {
                    "start_date":
                        "2026-07-01",

                    "end_date":
                        "2026-07-05",
                },
            )
        )

        print(
            "is_error:",
            range_result.is_error,
        )

        print(
            "structured_content:"
        )

        print(
            json.dumps(
                range_result.structured_content,
                ensure_ascii=False,
                indent=2,
            )
        )

        print(
            "content:"
        )

        for item in range_result.content:
            print(item)


if __name__ == "__main__":
    asyncio.run(main())