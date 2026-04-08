(function () {
  const birthStorageKey = "wuxing.birth.cache.v1";

  const birthFields = {
    year: document.getElementById("birth-year"),
    month: document.getElementById("birth-month"),
    day: document.getElementById("birth-day"),
    hour: document.getElementById("birth-hour"),
    minute: document.getElementById("birth-minute"),
  };

  const queryFields = {
    year: document.getElementById("query-year"),
    month: document.getElementById("query-month"),
    day: document.getElementById("query-day"),
  };

  const lookupButton = document.getElementById("lookup-button");
  const statusText = document.getElementById("status-text");
  const resultEmpty = document.getElementById("result-empty");
  const resultCard = document.getElementById("result-card");
  const favSummary = document.getElementById("fav-summary");
  const datePillars = document.getElementById("date-pillars");
  const dateElements = document.getElementById("date-elements");
  const rankingList = document.getElementById("ranking-list");

  function pad2(value) {
    return String(value).padStart(2, "0");
  }

  function daysInMonth(year, month) {
    return new Date(year, month, 0).getDate();
  }

  function fillSelect(select, values, formatter) {
    select.innerHTML = "";
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = String(value);
      option.textContent = formatter ? formatter(value) : String(value);
      select.appendChild(option);
    });
  }

  function buildRange(start, end) {
    const values = [];
    for (let value = start; value <= end; value += 1) {
      values.push(value);
    }
    return values;
  }

  function updateDayOptions(fields, selectedDay) {
    const year = Number(fields.year.value);
    const month = Number(fields.month.value);
    const maxDay = daysInMonth(year, month);
    fillSelect(fields.day, buildRange(1, maxDay), (value) => `${value}日`);
    fields.day.value = String(Math.min(selectedDay || 1, maxDay));
  }

  function saveBirthCache() {
    const payload = {
      year: birthFields.year.value,
      month: birthFields.month.value,
      day: birthFields.day.value,
      hour: birthFields.hour.value,
      minute: birthFields.minute.value,
    };
    localStorage.setItem(birthStorageKey, JSON.stringify(payload));
  }

  function initBirthSelectors(today) {
    fillSelect(
      birthFields.year,
      buildRange(today.getFullYear() - 120, today.getFullYear()),
      (value) => `${value}年`
    );
    fillSelect(birthFields.month, buildRange(1, 12), (value) => `${value}月`);
    fillSelect(birthFields.hour, buildRange(0, 23), (value) => `${pad2(value)}時`);
    fillSelect(
      birthFields.minute,
      buildRange(0, 59),
      (value) => `${pad2(value)}分`
    );

    const cached = JSON.parse(localStorage.getItem(birthStorageKey) || "null");
    const defaultBirth = cached || {
      year: "1996",
      month: "4",
      day: "27",
      hour: "17",
      minute: "30",
    };

    birthFields.year.value = defaultBirth.year;
    birthFields.month.value = defaultBirth.month;
    updateDayOptions(birthFields, Number(defaultBirth.day));
    birthFields.hour.value = defaultBirth.hour;
    birthFields.minute.value = defaultBirth.minute;

    Object.values(birthFields).forEach((field) => {
      field.addEventListener("change", () => {
        if (field === birthFields.year || field === birthFields.month) {
          updateDayOptions(birthFields, Number(birthFields.day.value));
        }
        saveBirthCache();
      });
    });

    saveBirthCache();
  }

  function initQuerySelectors(today) {
    fillSelect(
      queryFields.year,
      buildRange(today.getFullYear() - 10, today.getFullYear() + 10),
      (value) => `${value}年`
    );
    fillSelect(queryFields.month, buildRange(1, 12), (value) => `${value}月`);

    queryFields.year.value = String(today.getFullYear());
    queryFields.month.value = String(today.getMonth() + 1);
    updateDayOptions(queryFields, today.getDate());

    [queryFields.year, queryFields.month].forEach((field) => {
      field.addEventListener("change", () => {
        updateDayOptions(queryFields, Number(queryFields.day.value));
      });
    });
  }

  function setStatus(message, isError) {
    statusText.textContent = message;
    statusText.style.color = isError ? "#9d2d1a" : "";
  }

  function buildPayload() {
    return {
      birth: {
        year: birthFields.year.value,
        month: birthFields.month.value,
        day: birthFields.day.value,
        hour: birthFields.hour.value,
        minute: birthFields.minute.value,
      },
      target_date: {
        year: queryFields.year.value,
        month: queryFields.month.value,
        day: queryFields.day.value,
      },
    };
  }

  function renderResult(data) {
    favSummary.textContent = data.fav_summary;
    datePillars.textContent = data.date_pillars;
    dateElements.textContent = data.date_elements;
    rankingList.innerHTML = "";

    data.ranking.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item.label;
      rankingList.appendChild(li);
    });

    resultEmpty.classList.add("is-hidden");
    resultCard.classList.remove("is-hidden");
  }

  async function lookup() {
    setStatus("查詢中...", false);
    lookupButton.disabled = true;

    try {
      saveBirthCache();

      const response = await fetch("/api/score", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(buildPayload()),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "查詢失敗");
      }

      renderResult(data);
      setStatus("查詢完成。", false);
    } catch (error) {
      setStatus(error.message || "查詢失敗", true);
    } finally {
      lookupButton.disabled = false;
    }
  }

  const today = new Date();
  initBirthSelectors(today);
  initQuerySelectors(today);
  lookupButton.addEventListener("click", lookup);
})();
