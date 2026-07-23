const form = document.querySelector("#contact-form");
const submitButton = form.querySelector("button[type='submit']");
const resultBox = document.querySelector("#form-result");
const comment = form.elements.comment;
const commentCount = document.querySelector("#comment-count");
const healthDot = document.querySelector("#health-dot");
const healthText = document.querySelector("#health-text");

const setResult = (message, type) => {
  resultBox.textContent = message;
  resultBox.className = `form-result ${type}`;
};

const formatValidationError = (body) => {
  const details = body?.error?.details;
  if (!Array.isArray(details) || details.length === 0) {
    return "Проверьте корректность заполненных полей.";
  }

  return details
    .map((item) => {
      const field = Array.isArray(item.location)
        ? item.location.at(-1)
        : "поле";
      return `${field}: ${item.message}`;
    })
    .join("; ");
};

const checkHealth = async () => {
  try {
    const response = await fetch("/api/health", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("API unavailable");

    healthDot.classList.add("online");
    healthText.textContent = "API работает";
  } catch {
    healthDot.classList.add("offline");
    healthText.textContent = "API временно недоступен";
  }
};

comment.addEventListener("input", () => {
  commentCount.textContent = String(comment.value.length);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultBox.className = "form-result";

  if (!form.reportValidity()) return;

  const payload = Object.fromEntries(new FormData(form).entries());
  submitButton.disabled = true;
  submitButton.classList.add("loading");

  try {
    const response = await fetch("/api/contact", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));

    if (response.status === 201) {
      const aiNote =
        body.ai_status === "fallback"
          ? " AI-провайдер недоступен, использован резервный анализ."
          : "";
      const emailNote =
        body.owner_email_status === "sent" && body.user_email_status === "sent"
          ? " Подтверждение отправлено на email."
          : " Обращение сохранено, но часть email-уведомлений не отправлена.";

      setResult(`Спасибо! Обращение принято.${aiNote}${emailNote}`, "success");
      form.reset();
      commentCount.textContent = "0";
      return;
    }

    if (response.status === 422) {
      setResult(formatValidationError(body), "error");
    } else if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      const suffix = retryAfter ? ` Повторите через ${retryAfter} сек.` : "";
      setResult(`Слишком много запросов.${suffix}`, "error");
    } else if (response.status === 503) {
      setResult("Сервис временно недоступен. Попробуйте немного позже.", "error");
    } else {
      setResult("Не удалось отправить обращение. Попробуйте ещё раз.", "error");
    }
  } catch {
    setResult("Нет соединения с API. Проверьте сеть и повторите попытку.", "error");
  } finally {
    submitButton.disabled = false;
    submitButton.classList.remove("loading");
  }
});

checkHealth();
