"use client";

import { SetupState } from "../setup-state";
import { PageErrorState, PageLoadingState } from "../request-state";
import { RecommendationsView } from "../views/recommendations-view";
import { ApiRequestError, apiClient, isDataNotReadyError } from "../../lib/api";
import { useApiResource } from "../../lib/use-api-resource";

export function RecommendationsScreen() {
  const { data, error, loading, reload } = useApiResource(
    () => apiClient.getRetentionTargets(5, 3),
    [],
  );

  if (loading && !data) {
    return (
      <PageLoadingState
        title="Собираем retention-подборки"
        detail="Подтягиваем high-risk клиентов и готовые безопасные офферы для реактивации."
      />
    );
  }

  if (error) {
    if (isDataNotReadyError(error)) {
      return (
        <SetupState
          title="Retention-рекомендации пока не построены"
          detail={error.detail}
        />
      );
    }

    return (
      <PageErrorState
        title="Не удалось загрузить retention-рекомендации"
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

  return <RecommendationsView targets={data} />;
}
