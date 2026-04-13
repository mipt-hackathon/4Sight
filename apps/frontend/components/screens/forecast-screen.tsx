"use client";

import { SetupState } from "../setup-state";
import { PageErrorState, PageLoadingState } from "../request-state";
import { ForecastView } from "../views/forecast-view";
import { ApiRequestError, apiClient, isDataNotReadyError } from "../../lib/api";
import { useApiResource } from "../../lib/use-api-resource";

export function ForecastScreen() {
  const { data, error, loading, reload } = useApiResource(
    () => apiClient.getSalesForecast(21),
    [],
  );

  if (loading && !data) {
    return (
      <PageLoadingState
        title="Считаем прогноз продаж"
        detail="Загружаем исторический ряд и прогнозный горизонт для планирования закупок."
      />
    );
  }

  if (error) {
    if (isDataNotReadyError(error)) {
      return (
        <SetupState
          title="Прогноз продаж пока недоступен"
          detail={error.detail}
        />
      );
    }

    return (
      <PageErrorState
        title="Не удалось загрузить прогноз"
        detail={
          error instanceof ApiRequestError
            ? error.message
            : "Неожиданная ошибка загрузки данных."
        }
        onRetry={reload}
      />
    );
  }

  if (!data) {
    return null;
  }

  return <ForecastView forecast={data} />;
}
