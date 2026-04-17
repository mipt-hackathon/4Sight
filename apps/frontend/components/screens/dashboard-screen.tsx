"use client";

import { SetupState } from "../setup-state";
import { PageErrorState, PageLoadingState } from "../request-state";
import { DashboardView } from "../views/dashboard-view";
import { ApiRequestError, apiClient, isDataNotReadyError } from "../../lib/api";
import { useApiResource } from "../../lib/use-api-resource";

export function DashboardScreen() {
  const { data, error, loading, reload } = useApiResource(
    () => apiClient.getDashboardOverview(),
    [],
  );

  if (loading && !data) {
    return (
      <PageLoadingState
        title="Поднимаем KPI-контур"
        detail="Подтягиваем продажи, churn map, логистику и product quality сигналы."
      />
    );
  }

  if (error) {
    if (isDataNotReadyError(error)) {
      return (
        <SetupState
          title="Дашборд пока пустой: витрины не построены"
          detail={error.detail}
        />
      );
    }

    return (
      <PageErrorState
        title="Не удалось загрузить dashboard"
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

  return <DashboardView overview={data} />;
}
