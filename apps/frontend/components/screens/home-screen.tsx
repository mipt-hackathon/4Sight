"use client";

import { SetupState } from "../setup-state";
import { PageErrorState, PageLoadingState } from "../request-state";
import { HomeView } from "../views/home-view";
import { ApiRequestError, apiClient, isDataNotReadyError } from "../../lib/api";
import { useApiResource } from "../../lib/use-api-resource";

export function HomeScreen() {
  const { data, error, loading, reload } = useApiResource(async () => {
    const [overview, highRisk] = await Promise.all([
      apiClient.getDashboardOverview(),
      apiClient.getHighRiskCustomers(5),
    ]);
    return { overview, highRisk };
  }, []);

  if (loading && !data) {
    return (
      <PageLoadingState
        title="Собираем сигнал, риск и операционный контекст"
        detail="Загружаем KPI, очередь high-risk и quality watchlist поверх product backend."
      />
    );
  }

  if (error) {
    if (isDataNotReadyError(error)) {
      return (
        <SetupState
          title="Продуктовый dashboard еще не наполнен данными"
          detail={error.detail}
        />
      );
    }

    return (
      <PageErrorState
        title="Не удалось собрать главный экран"
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

  return <HomeView overview={data.overview} highRisk={data.highRisk} />;
}
