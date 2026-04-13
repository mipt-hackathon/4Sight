"use client";

import { SetupState } from "../setup-state";
import { PageErrorState, PageLoadingState } from "../request-state";
import { CustomerView } from "../views/customer-view";
import { ApiRequestError, apiClient, isDataNotReadyError } from "../../lib/api";
import { useApiResource } from "../../lib/use-api-resource";

type CustomerScreenProps = {
  userId: number;
};

export function CustomerScreen({ userId }: CustomerScreenProps) {
  const { data, error, loading, reload } = useApiResource(async () => {
    const [profile, churn, recommendations] = await Promise.all([
      apiClient.getCustomerProfile(userId),
      apiClient.getCustomerChurn(userId),
      apiClient.getCustomerRecommendations(userId, 5),
    ]);
    return { profile, churn, recommendations };
  }, [userId]);

  if (loading && !data) {
    return (
      <PageLoadingState
        title={`Собираем Customer 360 для клиента #${userId}`}
        detail="Подтягиваем профиль, поведение, churn-сигнал и next best action."
      />
    );
  }

  if (error) {
    if (isDataNotReadyError(error)) {
      return (
        <SetupState
          title={`Карточка клиента ${userId} пока недоступна`}
          detail={error.detail}
        />
      );
    }

    return (
      <PageErrorState
        title={`Не удалось загрузить клиента #${userId}`}
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

  return (
    <CustomerView
      userId={userId}
      profile={data.profile}
      churn={data.churn}
      recommendations={data.recommendations}
    />
  );
}
