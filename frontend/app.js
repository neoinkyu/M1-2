const API_BASE_URL =
  window.APP_CONFIG.API_BASE_URL;


// ==================================================
// 전역 상태
// ==================================================

let currentConversationId = null;

let cachedData = [];

let trendChart = null;

let editingDocumentId = null;


// ==================================================
// 공통 API 호출
// ==================================================

async function api(
  path,
  options = {}
) {

  const response =
    await fetch(
      `${API_BASE_URL}${path}`,
      {
        headers: {
          "Content-Type":
            "application/json",

          ...(options.headers || {})
        },

        ...options
      }
    );


  if (!response.ok) {

    let message =
      `API 오류 (${response.status})`;

    try {

      const error =
        await response.json();

      if (error.detail) {
        message =
          error.detail;
      }

    } catch (error) {

      // JSON 형식의 오류가 아닌 경우
      // 기본 오류 메시지 사용
    }


    throw new Error(
      message
    );
  }


  return response.json();
}


// ==================================================
// 데이터 요약
// ==================================================

async function loadSummary() {

  const summaryElement =
    document.getElementById(
      "summary"
    );


  try {

    const summary =
      await api(
        "/api/data/summary"
      );


    const metrics =
      summary.metrics || {};


    const trend =
      summary.trend || {};


    const comparison =
      summary.comparison || {};


    summaryElement.innerHTML = `

      <div class="summary-card">
        데이터 기간

        <strong>
          ${summary.period?.start || "-"}
          ~
          ${summary.period?.end || "-"}
        </strong>
      </div>


      <div class="summary-card">
        데이터 수

        <strong>
          ${summary.count ?? 0}건
        </strong>
      </div>


      <div class="summary-card">
        평균 PV

        <strong>
          ${formatNumber(
            metrics.average_pv
          )}
        </strong>
      </div>


      <div class="summary-card">
        평균 사용자

        <strong>
          ${formatNumber(
            metrics.average_users
          )}
        </strong>
      </div>


      <div class="summary-card">
        평균 클릭

        <strong>
          ${formatNumber(
            metrics.average_clicks
          )}
        </strong>
      </div>


      <div class="summary-card">
        평균 CTR

        <strong>
          ${formatPercent(
            metrics.average_ctr
          )}
        </strong>
      </div>


      <div class="summary-card">
        PV 추세

        <strong>
          ${trend.pv ?? "-"}
        </strong>
      </div>


      <div class="summary-card">
        클릭 추세

        <strong>
          ${trend.gsc_clicks ?? "-"}
        </strong>
      </div>


      <div class="summary-card">
        최근 PV 증감

        <strong>
          ${formatChange(
            comparison.pv_change_rate
          )}
        </strong>
      </div>


      <div class="summary-card">
        최근 사용자 증감

        <strong>
          ${formatChange(
            comparison.users_change_rate
          )}
        </strong>
      </div>


      <div class="summary-card">
        최근 클릭 증감

        <strong>
          ${formatChange(
            comparison.clicks_change_rate
          )}
        </strong>
      </div>


      <div class="summary-card">
        최근 노출 증감

        <strong>
          ${formatChange(
            comparison.impressions_change_rate
          )}
        </strong>
      </div>

    `;

  } catch (error) {

    summaryElement.textContent =
      `요약 정보를 불러오지 못했습니다: ${error.message}`;
  }
}


// ==================================================
// AI 채팅
// ==================================================

const chatForm =
  document.getElementById(
    "chat-form"
  );


chatForm.addEventListener(
  "submit",
  async (event) => {

    event.preventDefault();


    const input =
      document.getElementById(
        "chat-input"
      );


    const message =
      input.value.trim();


    if (!message) {
      return;
    }


    addChatMessage(
      "user",
      message
    );


    input.value =
      "";


    setLoading(
      true
    );


    try {

      const body = {
        message
      };


      if (
        currentConversationId
      ) {

        body.conversation_id =
          currentConversationId;
      }


      const response =
        await api(
          "/api/chat",
          {
            method:
              "POST",

            body:
              JSON.stringify(
                body
              )
          }
        );


      currentConversationId =
        response.conversation_id;


      addChatMessage(
        "assistant",
        response.answer
      );


      await loadConversations();

    } catch (error) {

      addChatMessage(
        "assistant",
        `오류가 발생했습니다: ${error.message}`
      );

    } finally {

      setLoading(
        false
      );
    }
  }
);


// ==================================================
// Markdown 보정
// ==================================================

function normalizeAssistantMarkdown(
  content
) {

  if (!content) {
    return "";
  }


  return content

    .replace(
      /\\\*/g,
      "*"
    )

    .replace(
      /\\~/g,
      "~"
    )

    .replace(
      /\\#/g,
      "#"
    )

    .replace(
      /\\`/g,
      "`"
    )

    .replace(
      /(\d+(?:\.\d+)?)~~(\d+(?:\.\d+)?)/g,
      "$1~$2"
    )

    .replace(
      /(\d{1,2}\/\d{1,2})~~(\d{1,2}\/\d{1,2})/g,
      "$1~$2"
    );
}


// ==================================================
// 채팅 메시지 출력
// ==================================================

function addChatMessage(
  role,
  content
) {

  const container =
    document.getElementById(
      "chat-messages"
    );


  const element =
    document.createElement(
      "div"
    );


  element.className =
    role === "user"
      ? "user-message"
      : "assistant-message";


  if (
    role === "user"
  ) {

    element.textContent =
      content;

  } else {

    const normalizedContent =
      normalizeAssistantMarkdown(
        content
      );


    const html =
      marked.parse(
        normalizedContent
      );


    element.innerHTML =
      DOMPurify.sanitize(
        html
      );
  }


  container.appendChild(
    element
  );


  container.scrollTop =
    container.scrollHeight;
}


// ==================================================
// 채팅 로딩
// ==================================================

function setLoading(
  show
) {

  document
    .getElementById(
      "loading"
    )
    .classList
    .toggle(
      "hidden",
      !show
    );
}


// ==================================================
// 대화 목록
// ==================================================

async function loadConversations() {

  const container =
    document.getElementById(
      "conversation-list"
    );


  try {

    const conversations =
      await api(
        "/api/conversations"
      );


    container.innerHTML =
      "";


    if (
      !conversations.length
    ) {

      container.textContent =
        "저장된 대화가 없습니다.";

      return;
    }


    conversations.forEach(
      conversation => {

        const element =
          document.createElement(
            "div"
          );


        element.className =
          "conversation-item";


        element.textContent =
          conversation.title;


        element.addEventListener(
          "click",
          () => {

            loadConversation(
              conversation.id
            );

          }
        );


        container.appendChild(
          element
        );
      }
    );

  } catch (error) {

    container.textContent =
      `대화 목록 오류: ${error.message}`;
  }
}


// ==================================================
// 특정 대화
// ==================================================

async function loadConversation(
  id
) {

  try {

    const conversation =
      await api(
        `/api/conversations/${id}`
      );


    currentConversationId =
      id;


    const container =
      document.getElementById(
        "chat-messages"
      );


    container.innerHTML =
      "";


    conversation.messages.forEach(
      message => {

        addChatMessage(
          message.role,
          message.content
        );

      }
    );

  } catch (error) {

    alert(
      `대화를 불러오지 못했습니다: ${error.message}`
    );
  }
}


// ==================================================
// 새 대화
// ==================================================

document
  .getElementById(
    "new-chat-button"
  )
  .addEventListener(
    "click",
    () => {

      currentConversationId =
        null;


      document
        .getElementById(
          "chat-messages"
        )
        .innerHTML = `
          <div class="assistant-message">
            새로운 대화를 시작합니다.
            옥션슈트 데이터에 대해 질문해 주세요.
          </div>
        `;
    }
  );


// ==================================================
// 데이터 조회
// ==================================================

async function loadData() {

  const tableBody =
    document.getElementById(
      "data-table-body"
    );


  try {

    const data =
      await api(
        "/api/data"
      );


    cachedData =
      data;


    renderChart();


    tableBody.innerHTML =
      "";


    [...data]
      .reverse()
      .forEach(
        row => {

          const tr =
            document.createElement(
              "tr"
            );


          tr.innerHTML = `

            <td>
              ${row.date ?? "-"}
            </td>


            <td>
              ${row.posts ?? "-"}
            </td>


            <td>
              ${row.pages ?? "-"}
            </td>


            <td>
              ${row.users ?? "-"}
            </td>


            <td>
              ${row.pv ?? row.value ?? "-"}
            </td>


            <td>
              ${formatMoney(
                row.adsense_estimated
              )}
            </td>


            <td>
              ${row.gsc_clicks ?? "-"}
            </td>


            <td>
              ${row.gsc_impressions ?? "-"}
            </td>


            <td>
              ${formatPercent(
                row.gsc_ctr
              )}
            </td>


            <td>
              ${formatNumber(
                row.gsc_position
              )}
            </td>


            <td>
              ${escapeHtml(
                row.memo ?? ""
              )}
            </td>


            <td>

              <button
                class="edit-button"
                data-id="${row.id}"
                type="button"
              >
                수정
              </button>


              <button
                class="delete-button"
                data-id="${row.id}"
                type="button"
              >
                삭제
              </button>

            </td>
          `;


          tableBody.appendChild(
            tr
          );
        }
      );


    // 수정 버튼 이벤트

    document
      .querySelectorAll(
        ".edit-button"
      )
      .forEach(
        button => {

          button.addEventListener(
            "click",
            () => {

              startEditData(
                button.dataset.id
              );

            }
          );
        }
      );


    // 삭제 버튼 이벤트

    document
      .querySelectorAll(
        ".delete-button"
      )
      .forEach(
        button => {

          button.addEventListener(
            "click",
            () => {

              deleteData(
                button.dataset.id
              );

            }
          );
        }
      );

  } catch (error) {

    tableBody.innerHTML = `
      <tr>
        <td colspan="12">
          데이터를 불러오지 못했습니다:
          ${error.message}
        </td>
      </tr>
    `;
  }
}


// ==================================================
// 수정 시작
// ==================================================

function startEditData(
  id
) {

  const row =
    cachedData.find(
      item =>
        item.id === id
    );


  if (!row) {

    alert(
      "수정할 데이터를 찾을 수 없습니다."
    );

    return;
  }


  editingDocumentId =
    id;


  document.getElementById(
    "data-date"
  ).value =
    row.date || id;


  document.getElementById(
    "data-posts"
  ).value =
    row.posts ?? "";


  document.getElementById(
    "data-pages"
  ).value =
    row.pages ?? "";


  document.getElementById(
    "data-users"
  ).value =
    row.users ?? "";


  document.getElementById(
    "data-pv"
  ).value =
    row.pv ??
    row.value ??
    "";


  document.getElementById(
    "data-adsense"
  ).value =
    row.adsense_estimated ?? "";


  document.getElementById(
    "data-gsc-clicks"
  ).value =
    row.gsc_clicks ?? "";


  document.getElementById(
    "data-gsc-impressions"
  ).value =
    row.gsc_impressions ?? "";


  // Firestore에서는 0.0161
  // 화면에서는 1.61%

  document.getElementById(
    "data-gsc-ctr"
  ).value =
    row.gsc_ctr !== null &&
    row.gsc_ctr !== undefined
      ? (
          Number(
            row.gsc_ctr
          ) * 100
        ).toFixed(2)
      : "";


  document.getElementById(
    "data-gsc-position"
  ).value =
    row.gsc_position ?? "";


  document.getElementById(
    "data-memo"
  ).value =
    row.memo ?? "";


  // 날짜 = Firestore 문서 ID
  // 수정 금지

  document.getElementById(
    "data-date"
  ).disabled =
    true;


  document.getElementById(
    "data-submit-button"
  ).textContent =
    "수정 저장";


  document.getElementById(
    "edit-cancel-button"
  ).classList.remove(
    "hidden"
  );


  const status =
    document.getElementById(
      "edit-status"
    );


  status.textContent =
    `${id} 데이터를 수정 중입니다.`;


  status.classList.remove(
    "hidden"
  );


  document.getElementById(
    "data-pv"
  ).focus();
}


// ==================================================
// 수정 취소
// ==================================================

function cancelEditData() {

  editingDocumentId =
    null;


  const form =
    document.getElementById(
      "data-form"
    );


  form.reset();


  document.getElementById(
    "data-date"
  ).disabled =
    false;


  document.getElementById(
    "data-submit-button"
  ).textContent =
    "추가";


  document.getElementById(
    "edit-cancel-button"
  ).classList.add(
    "hidden"
  );


  document.getElementById(
    "edit-status"
  ).classList.add(
    "hidden"
  );
}


document
  .getElementById(
    "edit-cancel-button"
  )
  .addEventListener(
    "click",
    cancelEditData
  );


// ==================================================
// 숫자 입력 보조 함수
// ==================================================

function getOptionalNumber(
  elementId
) {

  const value =
    document
      .getElementById(
        elementId
      )
      .value
      .trim();


  if (
    value === ""
  ) {

    return undefined;
  }


  const number =
    Number(
      value
    );


  if (
    Number.isNaN(
      number
    )
  ) {

    return undefined;
  }


  return number;
}


// ==================================================
// 데이터 폼 → API payload
// ==================================================

function buildDataPayload() {

  const pv =
    Number(
      document.getElementById(
        "data-pv"
      ).value
    );


  const ctrPercent =
    getOptionalNumber(
      "data-gsc-ctr"
    );


  const payload = {

    // 과제 필수 value는
    // PV와 항상 동일하게 유지

    value:
      pv,

    pv:
      pv,

    memo:
      document
        .getElementById(
          "data-memo"
        )
        .value
        .trim(),

    gsc_type:
      "web"
  };


  const posts =
    getOptionalNumber(
      "data-posts"
    );


  const pages =
    getOptionalNumber(
      "data-pages"
    );


  const users =
    getOptionalNumber(
      "data-users"
    );


  const adsense =
    getOptionalNumber(
      "data-adsense"
    );


  const clicks =
    getOptionalNumber(
      "data-gsc-clicks"
    );


  const impressions =
    getOptionalNumber(
      "data-gsc-impressions"
    );


  const position =
    getOptionalNumber(
      "data-gsc-position"
    );


  if (
    posts !== undefined
  ) {

    payload.posts =
      posts;
  }


  if (
    pages !== undefined
  ) {

    payload.pages =
      pages;
  }


  if (
    users !== undefined
  ) {

    payload.users =
      users;
  }


  if (
    adsense !== undefined
  ) {

    payload.adsense_estimated =
      adsense;
  }


  if (
    clicks !== undefined
  ) {

    payload.gsc_clicks =
      clicks;
  }


  if (
    impressions !== undefined
  ) {

    payload.gsc_impressions =
      impressions;
  }


  if (
    ctrPercent !== undefined
  ) {

    payload.gsc_ctr =
      ctrPercent / 100;
  }


  if (
    position !== undefined
  ) {

    payload.gsc_position =
      position;
  }


  return payload;
}


// ==================================================
// 데이터 추가 / 수정
// ==================================================

document
  .getElementById(
    "data-form"
  )
  .addEventListener(
    "submit",
    async (event) => {

      event.preventDefault();


      const date =
        document.getElementById(
          "data-date"
        ).value;


      const pv =
        Number(
          document.getElementById(
            "data-pv"
          ).value
        );


      if (
        Number.isNaN(
          pv
        )
      ) {

        alert(
          "PV를 숫자로 입력해 주세요."
        );

        return;
      }


      const payload =
        buildDataPayload();


      try {

        // ==========================================
        // 수정
        // ==========================================

        if (
          editingDocumentId
        ) {

          await api(
            `/api/data/${editingDocumentId}`,
            {
              method:
                "PUT",

              body:
                JSON.stringify(
                  payload
                )
            }
          );


          alert(
            `${editingDocumentId} 데이터가 수정되었습니다.`
          );


          cancelEditData();

        }


        // ==========================================
        // 추가
        // ==========================================

        else {

          payload.date =
            date;


          await api(
            "/api/data",
            {
              method:
                "POST",

              body:
                JSON.stringify(
                  payload
                )
            }
          );


          event.target.reset();
        }


        await Promise.all([
          loadData(),
          loadSummary()
        ]);

      } catch (error) {

        alert(
          editingDocumentId
            ? `데이터 수정 실패: ${error.message}`
            : `데이터 추가 실패: ${error.message}`
        );
      }
    }
  );


// ==================================================
// 데이터 삭제
// ==================================================

async function deleteData(
  id
) {

  const confirmed =
    confirm(
      `${id} 데이터를 삭제하시겠습니까?`
    );


  if (
    !confirmed
  ) {
    return;
  }


  try {

    await api(
      `/api/data/${id}`,
      {
        method:
          "DELETE"
      }
    );


    if (
      editingDocumentId === id
    ) {

      cancelEditData();
    }


    await Promise.all([
      loadData(),
      loadSummary()
    ]);

  } catch (error) {

    alert(
      `삭제 실패: ${error.message}`
    );
  }
}


// ==================================================
// 그래프
// ==================================================

function renderChart() {

  if (
    !cachedData.length
  ) {
    return;
  }


  const metric =
    document
      .getElementById(
        "chart-metric"
      )
      .value;


  const recentData =
    [...cachedData]
      .sort(
        (a, b) =>
          a.date.localeCompare(
            b.date
          )
      )
      .slice(-30);


  const labels =
    recentData.map(
      row =>
        row.date
    );


  const values =
    recentData.map(
      row =>
        row[metric] ?? null
    );


  const metricLabels = {

    pv:
      "PV",

    users:
      "사용자",

    gsc_clicks:
      "GSC 클릭",

    gsc_impressions:
      "GSC 노출",

    adsense_estimated:
      "AdSense 예상수익"
  };


  const canvas =
    document.getElementById(
      "trend-chart"
    );


  if (
    trendChart
  ) {

    trendChart.destroy();
  }


  trendChart =
    new Chart(
      canvas,
      {

        type:
          "line",

        data: {

          labels,

          datasets: [
            {

              label:
                metricLabels[
                  metric
                ],

              data:
                values,

              tension:
                0.2
            }
          ]
        },


        options: {

          responsive:
            true,

          maintainAspectRatio:
            false,


          interaction: {

            intersect:
              false,

            mode:
              "index"
          },


          scales: {

            x: {

              ticks: {

                maxTicksLimit:
                  10
              }
            }
          }
        }
      }
    );
}


document
  .getElementById(
    "chart-metric"
  )
  .addEventListener(
    "change",
    renderChart
  );


// ==================================================
// CSV 내보내기
// ==================================================

document
  .getElementById(
    "csv-button"
  )
  .addEventListener(
    "click",
    exportCsv
  );


function exportCsv() {

  if (
    !cachedData.length
  ) {

    alert(
      "내보낼 데이터가 없습니다."
    );

    return;
  }


  const columns = [

    "date",

    "value",

    "memo",

    "posts",

    "pages",

    "users",

    "pv",

    "adsense_estimated",

    "gsc_type",

    "gsc_clicks",

    "gsc_impressions",

    "gsc_ctr",

    "gsc_position"
  ];


  const rows = [

    columns,

    ...cachedData.map(
      row =>

        columns.map(
          column =>

            csvEscape(
              row[column] ?? ""
            )
        )
    )
  ];


  const csv =
    rows
      .map(
        row =>
          row.join(",")
      )
      .join("\n");


  const blob =
    new Blob(
      [
        "\uFEFF" + csv
      ],
      {
        type:
          "text/csv;charset=utf-8;"
      }
    );


  const url =
    URL.createObjectURL(
      blob
    );


  const link =
    document.createElement(
      "a"
    );


  link.href =
    url;


  link.download =
    `auctionsuit-data-${
      new Date()
        .toISOString()
        .slice(0, 10)
    }.csv`;


  document.body.appendChild(
    link
  );


  link.click();


  link.remove();


  URL.revokeObjectURL(
    url
  );
}


function csvEscape(
  value
) {

  const text =
    String(
      value
    );


  if (
    text.includes(",") ||
    text.includes("\"") ||
    text.includes("\n")
  ) {

    return `"${text.replace(
      /"/g,
      "\"\""
    )}"`;
  }


  return text;
}


// ==================================================
// 다크 모드
// ==================================================

const themeButton =
  document.getElementById(
    "theme-button"
  );


function applySavedTheme() {

  const savedTheme =
    localStorage.getItem(
      "theme"
    );


  if (
    savedTheme === "dark"
  ) {

    document
      .body
      .classList
      .add(
        "dark-mode"
      );


    themeButton.textContent =
      "라이트 모드";

  } else {

    themeButton.textContent =
      "다크 모드";
  }
}


themeButton.addEventListener(
  "click",
  () => {

    const isDark =
      document
        .body
        .classList
        .toggle(
          "dark-mode"
        );


    localStorage.setItem(
      "theme",
      isDark
        ? "dark"
        : "light"
    );


    themeButton.textContent =
      isDark
        ? "라이트 모드"
        : "다크 모드";


    renderChart();
  }
);


// ==================================================
// 표시 형식
// ==================================================

function formatPercent(
  value
) {

  if (
    value === null ||
    value === undefined
  ) {

    return "-";
  }


  const number =
    Number(
      value
    );


  if (
    Number.isNaN(
      number
    )
  ) {

    return "-";
  }


  return `${
    (
      number * 100
    ).toFixed(2)
  }%`;
}


function formatNumber(
  value
) {

  if (
    value === null ||
    value === undefined
  ) {

    return "-";
  }


  const number =
    Number(
      value
    );


  if (
    Number.isNaN(
      number
    )
  ) {

    return "-";
  }


  return number.toFixed(2);
}


function formatMoney(
  value
) {

  if (
    value === null ||
    value === undefined
  ) {

    return "-";
  }


  const number =
    Number(
      value
    );


  if (
    Number.isNaN(
      number
    )
  ) {

    return "-";
  }


  return number.toFixed(2);
}


function formatChange(
  value
) {

  if (
    value === null ||
    value === undefined
  ) {

    return "-";
  }


  const number =
    Number(
      value
    );


  if (
    Number.isNaN(
      number
    )
  ) {

    return "-";
  }


  const sign =
    number > 0
      ? "+"
      : "";


  return `${
    sign
  }${
    number.toFixed(2)
  }%`;
}


// ==================================================
// HTML escape
// ==================================================

function escapeHtml(
  value
) {

  const div =
    document.createElement(
      "div"
    );


  div.textContent =
    value;


  return div.innerHTML;
}


// ==================================================
// 초기화
// ==================================================

async function initialize() {

  applySavedTheme();


  await Promise.all([
    loadSummary(),
    loadData(),
    loadConversations()
  ]);
}


initialize();