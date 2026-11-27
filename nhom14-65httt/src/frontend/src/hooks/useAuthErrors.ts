import { useEffect, useState } from "react";
import { ApiError, errorMessage } from "../api/client";
import {
  authServerErrors,
  focusFirstError,
  type AuthErrors,
  type AuthFieldName,
} from "../utils/authValidation";

export function useAuthErrors(validation: AuthErrors) {
  const [touched, setTouched] = useState<
    Partial<Record<AuthFieldName, boolean>>
  >({});
  const [submitted, setSubmitted] = useState(false);
  const [server, setServer] = useState<AuthErrors>({});
  const [formError, setFormError] = useState("");
  const [focusTarget, setFocusTarget] = useState<{
    form: HTMLFormElement;
    fields: AuthErrors;
  } | null>(null);
  useEffect(() => {
    if (focusTarget) focusFirstError(focusTarget.form, focusTarget.fields);
  }, [focusTarget]);
  const errors = { ...server };
  for (const field of Object.keys(validation) as AuthFieldName[]) {
    if (submitted || touched[field]) errors[field] = validation[field];
  }
  function clear(field: AuthFieldName) {
    setServer((previous) => ({ ...previous, [field]: undefined }));
    setFormError("");
  }
  function check(form: HTMLFormElement) {
    setSubmitted(true);
    setServer({});
    setFormError("");
    if (!Object.keys(validation).length) return true;
    focusFirstError(form, validation);
    return false;
  }
  function fail(error: unknown, form: HTMLFormElement) {
    const fields = authServerErrors(error);
    setServer(fields);
    setFormError(
      Object.keys(fields).length
        ? ""
        : error instanceof ApiError && error.code === "AUTH_NOT_CONFIGURED"
          ? "Dịch vụ đăng nhập chưa sẵn sàng. Vui lòng thử lại sau."
          : errorMessage(error),
    );
    setFocusTarget({ form, fields });
  }
  return {
    errors,
    formError,
    clear,
    check,
    fail,
    touch: (field: AuthFieldName) =>
      setTouched((previous) => ({ ...previous, [field]: true })),
  };
}
