import { notFound } from "next/navigation";

import { CustomerScreen } from "../../../components/screens/customer-screen";

type CustomerPageProps = {
  params: {
    userId: string;
  };
};

export default function CustomerPage({ params }: CustomerPageProps) {
  const userId = Number(params.userId);
  if (!Number.isInteger(userId) || userId <= 0) {
    notFound();
  }

  return <CustomerScreen userId={userId} />;
}
