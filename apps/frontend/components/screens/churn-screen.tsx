"use client";

import { SetupState } from "../setup-state";
import { PageErrorState, PageLoadingState } from "../request-state";
import { ChurnView } from "../views/churn-view";
import { ApiRequestError, apiClient, isDataNotReadyError } from "../../lib/api";
import { useApiResource } from "../../lib/use-api-resource";

export function ChurnScreen() {
  const { data, error, loading, reload } = useApiResource(async () => {
    const [overview, highRisk] = await Promise.all([
      apiClient.getDashboardOverview(),
      apiClient.getHighRiskCustomers(20),
    ]);
    return { overview, highRisk };
  }, []);

  if (loading && !data) {
    return (
      <PageLoadingState
        title="Строим churn board"
        detail="Загружаем очередь high-risk и сегменты, где риск уже концентрируется."
      />
    );
  }

  if (error) {
    if (isDataNotReadyError(error)) {
      return (
        <SetupState
          title="Список churn-кандидатов пока недоступен"
          detail={error.detail}
        />
      );
    }

    return (
      <PageErrorState
        title="Не удалось загрузить churn board"
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

  return <ChurnView overview={data.overview} highRisk={data.highRisk} />;
}
